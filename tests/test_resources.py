"""Tests for API resource methods: cards, fonts, orders, etc."""

import json

import responses

from handwrytten.models import Recipient, Sender

BASE = "https://api.handwrytten.com/v2/"


# ---------------------------------------------------------------------------
# Cards
# ---------------------------------------------------------------------------

class TestCards:
    def test_list_returns_card_objects(self, client, mock_api):
        mock_api.get(
            BASE + "cards/list",
            json=[
                {"id": 100, "title": "Thank You", "product_type": "greeting"},
                {"id": 200, "title": "Birthday", "product_type": "birthday"},
            ],
        )

        cards = client.cards.list()

        assert len(cards) == 2
        assert cards[0].id == "100"
        assert cards[0].title == "Thank You"
        assert cards[0].category == "greeting"
        assert cards[1].title == "Birthday"

    def test_list_handles_wrapped_response(self, client, mock_api):
        mock_api.get(
            BASE + "cards/list",
            json={"results": [{"id": 1, "title": "Card A"}]},
        )

        cards = client.cards.list()

        assert len(cards) == 1
        assert cards[0].title == "Card A"

    def test_get_returns_single_card(self, client, mock_api):
        mock_api.get(
            BASE + "cards/get/42",
            json={"id": 42, "title": "Holiday", "cover": "https://img.com/holiday.jpg"},
        )

        card = client.cards.get("42")

        assert card.id == "42"
        assert card.title == "Holiday"
        assert card.image_url == "https://img.com/holiday.jpg"

    def test_raw_field_preserved(self, client, mock_api):
        mock_api.get(
            BASE + "cards/list",
            json=[{"id": 1, "title": "X", "some_extra_field": "hello"}],
        )

        cards = client.cards.list()

        assert cards[0].raw["some_extra_field"] == "hello"

    def test_categories(self, client, mock_api):
        mock_api.get(
            BASE + "cards/categories",
            json=[{"id": 1, "name": "Greeting"}, {"id": 2, "name": "Holiday"}],
        )

        cats = client.cards.categories()

        assert len(cats) == 2
        assert cats[0]["name"] == "Greeting"

    def test_categories_non_list_response(self, client, mock_api):
        mock_api.get(BASE + "cards/categories", json={"error": "unexpected"})

        cats = client.cards.categories()

        assert cats == []


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

class TestFonts:
    def test_list_returns_font_objects(self, client, mock_api):
        mock_api.get(
            BASE + "fonts/list",
            json=[
                {"id": 10, "name": "Classic", "preview_url": "https://img.com/classic.jpg"},
                {"id": 20, "name": "Modern"},
            ],
        )

        fonts = client.fonts.list()

        assert len(fonts) == 2
        assert fonts[0].id == "10"
        assert fonts[0].name == "Classic"
        assert fonts[0].preview_url == "https://img.com/classic.jpg"
        assert fonts[1].name == "Modern"

    def test_list_for_customizer_dict_response(self, client, mock_api):
        mock_api.get(
            BASE + "fonts/listForCustomizer",
            json={"fonts": [{"id": 1, "label": "Arial"}, {"id": 2, "label": "Helvetica"}]},
        )

        fonts = client.fonts.list_for_customizer()

        assert len(fonts) == 2
        assert fonts[0]["label"] == "Arial"

    def test_list_for_customizer_list_response(self, client, mock_api):
        mock_api.get(
            BASE + "fonts/listForCustomizer",
            json=[{"id": 1, "label": "Arial"}],
        )

        fonts = client.fonts.list_for_customizer()

        assert len(fonts) == 1


# ---------------------------------------------------------------------------
# Gift Cards
# ---------------------------------------------------------------------------

class TestGiftCards:
    def test_list(self, client, mock_api):
        mock_api.get(
            BASE + "giftCards/list",
            json=[{"id": 1, "title": "$25 Amazon", "amount": 25.0}],
        )

        items = client.gift_cards.list()

        assert len(items) == 1
        assert items[0].title == "$25 Amazon"
        assert items[0].amount == 25.0


# ---------------------------------------------------------------------------
# Inserts
# ---------------------------------------------------------------------------

class TestInserts:
    def test_list(self, client, mock_api):
        mock_api.get(
            BASE + "inserts/list",
            json=[{"id": 1, "title": "Business Card"}],
        )

        items = client.inserts.list()

        assert len(items) == 1
        assert items[0].title == "Business Card"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class TestAuth:
    def test_get_user(self, client, mock_api):
        mock_api.get(
            BASE + "auth/getUser",
            json={
                "id": "user_123",
                "email": "test@example.com",
                "firstName": "Jane",
                "lastName": "Doe",
                "credits": 42.5,
            },
        )

        user = client.auth.get_user()

        assert user.id == "user_123"
        assert user.email == "test@example.com"
        assert user.first_name == "Jane"
        assert user.credits == 42.5

    def test_login(self, client, mock_api):
        mock_api.post(
            BASE + "auth/authorization",
            json={"uid": "abc123", "session": "sess_xyz"},
        )

        result = client.auth.login("user@example.com", "password123")

        assert result["uid"] == "abc123"
        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["login"] == "user@example.com"
        assert sent["password"] == "password123"


# ---------------------------------------------------------------------------
# Orders (two-step: placeBasket + basket/send)
# ---------------------------------------------------------------------------

class TestOrders:
    def _mock_order_flow(self, mock_api, place_response=None, send_response=None):
        """Helper to mock both placeBasket and basket/send endpoints."""
        mock_api.post(
            BASE + "orders/placeBasket",
            json=place_response or {"order_id": "ord_abc"},
        )
        mock_api.post(
            BASE + "basket/send",
            json=send_response or {"id": "ord_abc", "status": "processing"},
        )

    def test_send_single_dict_recipient(self, client, mock_api):
        self._mock_order_flow(mock_api)

        result = client.orders.send(
            card_id="100",
            font="hwDavid",
            message="Thank you!",
            recipient={
                "firstName": "Jane",
                "lastName": "Doe",
                "street1": "123 Main St",
                "city": "Phoenix",
                "state": "AZ",
                "zip": "85001",
            },
        )

        assert result["status"] == "processing"

        # Verify placeBasket request
        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["card_id"] == 100
        assert sent["font"] == "hwDavid"
        assert len(sent["addresses"]) == 1
        addr = sent["addresses"][0]
        assert addr["to_first_name"] == "Jane"
        assert addr["to_address1"] == "123 Main St"
        assert addr["message"] == "Thank you!"

    def test_send_with_sender_dict(self, client, mock_api):
        self._mock_order_flow(mock_api)

        client.orders.send(
            card_id="100",
            font="hwDavid",
            message="Thanks!",
            sender={
                "firstName": "David",
                "lastName": "Wachs",
                "street1": "100 S Mill Ave",
                "city": "Tempe",
                "state": "AZ",
                "zip": "85281",
            },
            recipient={
                "firstName": "Jane",
                "lastName": "Doe",
                "street1": "123 Main",
                "city": "Phoenix",
                "state": "AZ",
                "zip": "85001",
            },
        )

        sent = json.loads(mock_api.calls[0].request.body)
        addr = sent["addresses"][0]
        assert addr["from_first_name"] == "David"
        assert addr["from_address1"] == "100 S Mill Ave"
        assert addr["to_first_name"] == "Jane"

    def test_send_with_sender_object(self, client, mock_api):
        self._mock_order_flow(mock_api)

        client.orders.send(
            card_id="100",
            font="hwDavid",
            message="Thanks!",
            sender=Sender(
                first_name="David", last_name="Wachs",
                street1="100 S Mill", city="Tempe", state="AZ", zip="85281",
            ),
            recipient=Recipient(
                first_name="Jane", last_name="Doe",
                street1="123 Main", city="Phoenix", state="AZ", zip="85001",
            ),
        )

        sent = json.loads(mock_api.calls[0].request.body)
        addr = sent["addresses"][0]
        assert addr["from_first_name"] == "David"
        assert addr["to_first_name"] == "Jane"

    def test_send_with_int_sender(self, client, mock_api):
        self._mock_order_flow(mock_api)

        client.orders.send(
            card_id="100",
            font="hwDavid",
            message="Thanks!",
            sender=12345,
            recipient={"firstName": "Jane", "lastName": "Doe",
                        "street1": "1", "city": "X", "state": "AZ", "zip": "85001"},
        )

        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["return_address_id"] == 12345

    def test_send_with_int_recipient(self, client, mock_api):
        self._mock_order_flow(mock_api)

        client.orders.send(
            card_id="100",
            font="hwDavid",
            message="Thanks!",
            recipient=67890,
        )

        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["addresses"][0]["address_id"] == 67890
        assert sent["addresses"][0]["message"] == "Thanks!"

    def test_send_bulk_recipients(self, client, mock_api):
        self._mock_order_flow(mock_api)

        client.orders.send(
            card_id="100",
            font="hwDavid",
            message="Default msg",
            recipient=[
                {
                    "firstName": "Jane",
                    "lastName": "Doe",
                    "street1": "123 Main",
                    "city": "Phoenix",
                    "state": "AZ",
                    "zip": "85001",
                    "message": "Custom for Jane!",
                },
                {
                    "firstName": "John",
                    "lastName": "Smith",
                    "street1": "456 Oak",
                    "city": "Tempe",
                    "state": "AZ",
                    "zip": "85281",
                },
            ],
        )

        sent = json.loads(mock_api.calls[0].request.body)
        assert len(sent["addresses"]) == 2
        # First recipient has custom message
        assert sent["addresses"][0]["message"] == "Custom for Jane!"
        # Second recipient gets default message
        assert sent["addresses"][1]["message"] == "Default msg"

    def test_send_bulk_mixed_types(self, client, mock_api):
        self._mock_order_flow(mock_api)

        client.orders.send(
            card_id="100",
            font="hwDavid",
            message="Hello!",
            recipient=[
                Recipient(
                    first_name="Jane", last_name="Doe",
                    street1="123 Main", city="Phoenix", state="AZ", zip="85001",
                ),
                67890,  # saved address ID
                {"firstName": "Bob", "lastName": "X", "street1": "1",
                 "city": "Y", "state": "AZ", "zip": "85001"},
            ],
        )

        sent = json.loads(mock_api.calls[0].request.body)
        assert len(sent["addresses"]) == 3
        assert sent["addresses"][0]["to_first_name"] == "Jane"
        assert sent["addresses"][1]["address_id"] == 67890
        assert sent["addresses"][2]["to_first_name"] == "Bob"

    def test_send_per_recipient_sender_override(self, client, mock_api):
        self._mock_order_flow(mock_api)

        client.orders.send(
            card_id="100",
            font="hwDavid",
            message="Hello!",
            sender={"firstName": "Default", "lastName": "Sender",
                    "street1": "1", "city": "X", "state": "AZ", "zip": "85001"},
            recipient=[
                {
                    "firstName": "Jane",
                    "lastName": "Doe",
                    "street1": "123 Main",
                    "city": "Phoenix",
                    "state": "AZ",
                    "zip": "85001",
                    "sender": {
                        "firstName": "Override",
                        "lastName": "Sender",
                        "street1": "999 Other",
                        "city": "Other",
                        "state": "CA",
                        "zip": "90001",
                    },
                },
                {
                    "firstName": "John",
                    "lastName": "Smith",
                    "street1": "456 Oak",
                    "city": "Tempe",
                    "state": "AZ",
                    "zip": "85281",
                },
            ],
        )

        sent = json.loads(mock_api.calls[0].request.body)
        # First recipient has override sender
        assert sent["addresses"][0]["from_first_name"] == "Override"
        # Second recipient gets default sender
        assert sent["addresses"][1]["from_first_name"] == "Default"

    def test_send_per_recipient_int_sender_override(self, client, mock_api):
        self._mock_order_flow(mock_api)

        client.orders.send(
            card_id="100",
            font="hwDavid",
            message="Hello!",
            recipient=[
                {
                    "firstName": "Jane",
                    "lastName": "Doe",
                    "street1": "123 Main",
                    "city": "Phoenix",
                    "state": "AZ",
                    "zip": "85001",
                    "sender": 99999,
                },
            ],
        )

        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["addresses"][0]["return_address_id"] == 99999

    def test_send_with_wishes(self, client, mock_api):
        self._mock_order_flow(mock_api)

        client.orders.send(
            card_id="100",
            font="hwDavid",
            message="Thanks!",
            wishes="Best,\nThe Team",
            recipient={"firstName": "J", "lastName": "D", "street1": "1",
                        "city": "X", "state": "AZ", "zip": "85001"},
        )

        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["addresses"][0]["wishes"] == "Best,\nThe Team"

    def test_send_with_optional_params(self, client, mock_api):
        self._mock_order_flow(mock_api)

        client.orders.send(
            card_id="100",
            font="hwDavid",
            message="Thanks!",
            recipient={"firstName": "J", "lastName": "D", "street1": "1",
                        "city": "X", "state": "AZ", "zip": "85001"},
            denomination_id=50,
            insert_id=10,
            font_size=14,
            auto_font_size=True,
            message_align="center",
            delivery_confirmation=True,
            client_metadata="meta123",
            signature_id=5,
            signature2_id=6,
        )

        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["denomination_id"] == 50
        assert sent["insert_id"] == 10
        assert sent["font_size"] == 14
        assert sent["auto_font_size"] is True
        assert sent["message_align"] == "center"
        assert sent["delivery_confirmation"] is True
        assert sent["client_metadata"] == "meta123"
        assert sent["signature_id"] == 5
        assert sent["signature2_id"] == 6

    def test_send_with_coupon_and_credit_card(self, client, mock_api):
        self._mock_order_flow(mock_api)

        client.orders.send(
            card_id="100",
            font="hwDavid",
            message="Thanks!",
            recipient={"firstName": "J", "lastName": "D", "street1": "1",
                        "city": "X", "state": "AZ", "zip": "85001"},
            coupon_code="SAVE10",
            credit_card_id=42,
        )

        # coupon_code goes to both placeBasket and basket/send
        place_body = json.loads(mock_api.calls[0].request.body)
        assert place_body["couponCode"] == "SAVE10"

        send_body = json.loads(mock_api.calls[1].request.body)
        assert send_body["couponCode"] == "SAVE10"
        assert send_body["credit_card_id"] == 42

    def test_send_recipient_with_to_prefix_passthrough(self, client, mock_api):
        self._mock_order_flow(mock_api)

        client.orders.send(
            card_id="100",
            font="hwDavid",
            message="Hi",
            recipient={"to_first_name": "Jane", "to_last_name": "Doe",
                        "to_address1": "123 Main", "to_city": "Phoenix",
                        "to_state": "AZ", "to_zip": "85001"},
        )

        sent = json.loads(mock_api.calls[0].request.body)
        addr = sent["addresses"][0]
        assert addr["to_first_name"] == "Jane"
        assert addr["to_address1"] == "123 Main"

    def test_list_orders(self, client, mock_api):
        mock_api.get(
            BASE + "orders/list",
            json=[
                {"id": "ord_1", "status": "delivered", "trackingNumber": "TRK123"},
                {"id": "ord_2", "status": "processing"},
            ],
        )

        orders = client.orders.list()

        assert len(orders) == 2
        assert orders[0].tracking_number == "TRK123"
        assert orders[1].status == "processing"

    def test_list_orders_with_pagination(self, client, mock_api):
        mock_api.get(BASE + "orders/list", json=[{"id": "1", "status": "ok"}])

        client.orders.list(page=2, per_page=10)

        assert "page=2" in mock_api.calls[0].request.url
        assert "per_page=10" in mock_api.calls[0].request.url

    def test_get_order(self, client, mock_api):
        mock_api.get(
            BASE + "orders/get/ord_abc",
            json={
                "id": "ord_abc",
                "status": "shipped",
                "message": "Thank you!",
                "createdAt": "2025-01-15T10:30:00Z",
            },
        )

        order = client.orders.get("ord_abc")

        assert order.id == "ord_abc"
        assert order.status == "shipped"
        assert order.created_at == "2025-01-15T10:30:00Z"

    def test_send_invalid_recipient_type_raises(self, client):
        import pytest
        with responses.RequestsMock() as rsps:
            with pytest.raises(TypeError, match="Each recipient must be"):
                client.orders.send(
                    card_id="100",
                    font="hwDavid",
                    message="Hi",
                    recipient=3.14,  # float is invalid
                )


# ---------------------------------------------------------------------------
# Basket
# ---------------------------------------------------------------------------

class TestBasket:
    def test_add_order_basic(self, client, mock_api):
        mock_api.post(
            BASE + "orders/placeBasket",
            json={"order_id": "ord_123"},
        )

        result = client.basket.add_order(
            card_id="100",
            message="Hello!",
            font="hwDavid",
            addresses=[{
                "to_first_name": "Jane",
                "to_last_name": "Doe",
                "to_address1": "123 Main",
                "to_city": "Phoenix",
                "to_state": "AZ",
                "to_zip": "85001",
            }],
        )

        assert result["order_id"] == "ord_123"
        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["card_id"] == 100
        assert sent["font"] == "hwDavid"
        assert sent["message"] == "Hello!"

    def test_add_order_friendly_address_conversion(self, client, mock_api):
        mock_api.post(BASE + "orders/placeBasket", json={"order_id": "1"})

        client.basket.add_order(
            card_id="100",
            addresses=[{
                "firstName": "Jane",
                "lastName": "Doe",
                "street1": "123 Main",
                "city": "Phoenix",
                "state": "AZ",
                "zip": "85001",
                "message": "Hi Jane!",
                "wishes": "Best,\nTeam",
            }],
        )

        sent = json.loads(mock_api.calls[0].request.body)
        addr = sent["addresses"][0]
        assert addr["to_first_name"] == "Jane"
        assert addr["to_last_name"] == "Doe"
        assert addr["to_address1"] == "123 Main"
        assert addr["to_city"] == "Phoenix"
        assert addr["message"] == "Hi Jane!"
        assert addr["wishes"] == "Best,\nTeam"

    def test_add_order_to_prefix_passthrough(self, client, mock_api):
        mock_api.post(BASE + "orders/placeBasket", json={"order_id": "1"})

        client.basket.add_order(
            card_id="100",
            addresses=[{"to_first_name": "Jane", "to_last_name": "Doe"}],
        )

        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["addresses"][0]["to_first_name"] == "Jane"

    def test_add_order_with_address_ids(self, client, mock_api):
        mock_api.post(BASE + "orders/placeBasket", json={"order_id": "1"})

        client.basket.add_order(card_id="100", address_ids=[123, 456])

        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["address_ids"] == [123, 456]

    def test_add_order_with_return_address_id(self, client, mock_api):
        mock_api.post(BASE + "orders/placeBasket", json={"order_id": "1"})

        client.basket.add_order(
            card_id="100",
            return_address_id=999,
            address_ids=[123],
        )

        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["return_address_id"] == 999

    def test_add_order_optional_params(self, client, mock_api):
        mock_api.post(BASE + "orders/placeBasket", json={"order_id": "1"})

        client.basket.add_order(
            card_id="100",
            font_size=14,
            auto_font_size=True,
            message_align="center",
            denomination_id=50,
            insert_id=10,
            signature_id=5,
            signature2_id=6,
            date_send="2025-06-01",
            coupon_code="SAVE10",
            delivery_confirmation=True,
            client_metadata="meta",
            suppress_warnings=True,
            address_ids=[1],
        )

        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["font_size"] == 14
        assert sent["auto_font_size"] is True
        assert sent["message_align"] == "center"
        assert sent["denomination_id"] == 50
        assert sent["insert_id"] == 10
        assert sent["signature_id"] == 5
        assert sent["signature2_id"] == 6
        assert sent["date_send"] == "2025-06-01"
        assert sent["couponCode"] == "SAVE10"
        assert sent["delivery_confirmation"] is True
        assert sent["client_metadata"] == "meta"
        assert sent["supressWarnings"] is True

    def test_send(self, client, mock_api):
        mock_api.post(
            BASE + "basket/send",
            json={"status": "ok", "total": 5.99},
        )

        result = client.basket.send()

        assert result["status"] == "ok"

    def test_send_with_params(self, client, mock_api):
        mock_api.post(BASE + "basket/send", json={"status": "ok"})

        client.basket.send(
            coupon_code="SAVE10",
            credit_card_id=42,
            test_mode=True,
            check_quantity=True,
            check_cass_before_submit=False,
        )

        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["couponCode"] == "SAVE10"
        assert sent["credit_card_id"] == 42
        assert sent["test_mode"] == 1
        assert sent["check_quantity"] is True
        assert sent["check_cass_before_submit"] == 0

    def test_remove(self, client, mock_api):
        mock_api.post(
            BASE + "basket/remove",
            json={"httpCode": 200, "status": "ok", "item": []},
        )

        result = client.basket.remove(basket_id=9517)

        assert result["status"] == "ok"
        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["id"] == 9517

    def test_clear(self, client, mock_api):
        mock_api.post(
            BASE + "basket/clear",
            json={"httpCode": 200, "status": "ok", "item": []},
        )

        result = client.basket.clear()

        assert result["status"] == "ok"

    def test_list(self, client, mock_api):
        mock_api.get(
            BASE + "basket/allNew",
            json={
                "httpCode": 200,
                "status": "ok",
                "totals": {"grand_total": 3.55},
                "test_mode": 0,
                "items": [
                    {"id": 44373, "basket_id": 9517, "status": "basket", "price": 3.0},
                ],
            },
        )

        result = client.basket.list()

        assert result["status"] == "ok"
        assert len(result["items"]) == 1
        assert result["items"][0]["basket_id"] == 9517
        assert result["totals"]["grand_total"] == 3.55

    def test_get_item(self, client, mock_api):
        mock_api.get(
            BASE + "basket/item",
            json={
                "httpCode": 200,
                "status": "ok",
                "item": {"id": "9519", "basket_id": 9519, "price": "3.7", "font": "hwJeff"},
            },
        )

        result = client.basket.get_item(basket_id=9519)

        assert result["status"] == "ok"
        assert result["item"]["font"] == "hwJeff"
        assert "id=9519" in mock_api.calls[0].request.url

    def test_count(self, client, mock_api):
        mock_api.get(
            BASE + "basket/count",
            json={"httpCode": 200, "status": "ok", "count": 3},
        )

        result = client.basket.count()

        assert result == 3

    def test_count_empty_basket(self, client, mock_api):
        mock_api.get(BASE + "basket/count", json={"httpCode": 200, "status": "ok", "count": 0})

        assert client.basket.count() == 0


# ---------------------------------------------------------------------------
# Address Book
# ---------------------------------------------------------------------------

class TestAddressBook:
    def test_countries(self, client, mock_api):
        mock_api.get(
            BASE + "countries/list",
            json=[
                {"code": "US", "name": "United States"},
                {"code": "CA", "name": "Canada"},
            ],
        )

        countries = client.address_book.countries()

        assert len(countries) == 2
        assert countries[0].code == "US"

    def test_states(self, client, mock_api):
        mock_api.get(
            BASE + "states/list",
            json=[
                {"abbreviation": "AZ", "name": "Arizona"},
                {"abbreviation": "CA", "name": "California"},
            ],
        )

        states = client.address_book.states("US")

        assert len(states) == 2
        assert states[0].code == "AZ"
        assert states[0].name == "Arizona"

    def test_list_recipients(self, client, mock_api):
        mock_api.get(
            BASE + "profile/recipientsList",
            json={"addresses": [
                {"id": 1, "first_name": "Jane", "last_name": "Doe",
                 "address1": "123 Main", "city": "Phoenix", "state": "AZ", "zip": "85001"},
            ]},
        )

        recipients = client.address_book.list_recipients()

        assert len(recipients) == 1
        assert recipients[0].id == 1
        assert recipients[0].first_name == "Jane"
        assert recipients[0].street1 == "123 Main"

    def test_list_recipients_list_response(self, client, mock_api):
        mock_api.get(
            BASE + "profile/recipientsList",
            json=[{"id": 1, "first_name": "Jane", "last_name": "Doe"}],
        )

        recipients = client.address_book.list_recipients()

        assert len(recipients) == 1

    def test_add_recipient(self, client, mock_api):
        mock_api.post(
            BASE + "profile/addRecipient",
            json={"address": {"id": 12345, "first_name": "Jane"}},
        )

        result = client.address_book.add_recipient(
            first_name="Jane",
            last_name="Doe",
            street1="123 Main St",
            city="Phoenix",
            state="AZ",
            zip="85001",
        )

        assert result == 12345
        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["first_name"] == "Jane"
        assert sent["address1"] == "123 Main St"

    def test_add_recipient_with_optional_fields(self, client, mock_api):
        mock_api.post(
            BASE + "profile/addRecipient",
            json={"address": {"id": 100}},
        )

        client.address_book.add_recipient(
            first_name="Jane",
            last_name="Doe",
            street1="123 Main",
            city="Phoenix",
            state="AZ",
            zip="85001",
            street2="Apt 4",
            company="Acme",
            country_id="US",
            birthday="01/15/1990",
            anniversary="06/01/2010",
            allow_poor=True,
        )

        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["address2"] == "Apt 4"
        assert sent["business_name"] == "Acme"
        assert sent["country_id"] == "US"
        assert sent["birthday"] == "01/15/1990"
        assert sent["anniversary"] == "06/01/2010"
        assert sent["allow_poor"] is True

    def test_update_recipient(self, client, mock_api):
        mock_api.put(
            BASE + "profile/updateRecipient",
            json={"address": {"id": 12345}},
        )

        result = client.address_book.update_recipient(
            address_id=12345,
            street1="456 New St",
            city="Scottsdale",
        )

        assert result == 12345
        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["id"] == 12345
        assert sent["address1"] == "456 New St"
        assert sent["city"] == "Scottsdale"
        # Fields not passed should not be in the body
        assert "first_name" not in sent
        assert "last_name" not in sent

    def test_update_recipient_all_fields(self, client, mock_api):
        mock_api.put(
            BASE + "profile/updateRecipient",
            json={"address": {"id": 100}},
        )

        client.address_book.update_recipient(
            address_id=100,
            first_name="Jane",
            last_name="Doe",
            street1="1",
            city="X",
            state="AZ",
            zip="85001",
            street2="Apt 1",
            company="Co",
            country_id="US",
            birthday="01/01",
            anniversary="06/01",
            allow_poor=False,
        )

        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["first_name"] == "Jane"
        assert sent["address1"] == "1"
        assert sent["address2"] == "Apt 1"
        assert sent["business_name"] == "Co"

    def test_list_senders(self, client, mock_api):
        mock_api.get(
            BASE + "profile/listAddresses",
            json={"addressses": [  # API typo: triple 's'
                {"id": 1, "first_name": "David", "last_name": "Wachs",
                 "address1": "100 S Mill", "city": "Tempe", "state": "AZ", "zip": "85281"},
            ]},
        )

        senders = client.address_book.list_senders()

        assert len(senders) == 1
        assert senders[0].first_name == "David"
        assert senders[0].street1 == "100 S Mill"

    def test_list_senders_addresses_key(self, client, mock_api):
        """Test fallback to 'addresses' key."""
        mock_api.get(
            BASE + "profile/listAddresses",
            json={"addresses": [{"id": 1, "first_name": "David"}]},
        )

        senders = client.address_book.list_senders()

        assert len(senders) == 1

    def test_add_sender(self, client, mock_api):
        mock_api.post(
            BASE + "profile/createAddress",
            json={"address": {"id": 56789, "first_name": "David"}},
        )

        result = client.address_book.add_sender(
            first_name="David",
            last_name="Wachs",
            street1="100 S Mill Ave",
            city="Tempe",
            state="AZ",
            zip="85281",
        )

        assert result == 56789
        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["first_name"] == "David"
        assert sent["address1"] == "100 S Mill Ave"

    def test_add_sender_with_optional_fields(self, client, mock_api):
        mock_api.post(
            BASE + "profile/createAddress",
            json={"address": {"id": 100}},
        )

        client.address_book.add_sender(
            first_name="David",
            last_name="Wachs",
            street1="1",
            city="X",
            state="AZ",
            zip="85001",
            street2="Suite 200",
            company="Handwrytten",
            country_id="US",
            default=True,
            allow_poor=False,
        )

        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["address2"] == "Suite 200"
        assert sent["business_name"] == "Handwrytten"
        assert sent["country_id"] == "US"
        assert sent["default"] is True
        assert sent["allow_poor"] is False

    def test_add_sender_nested_response_fallback(self, client, mock_api):
        """Test when API returns address_id instead of nested address."""
        mock_api.post(
            BASE + "profile/createAddress",
            json={"address_id": 777},
        )

        result = client.address_book.add_sender(
            first_name="D", last_name="W",
            street1="1", city="X", state="AZ", zip="85001",
        )

        assert result == 777


# ---------------------------------------------------------------------------
# Custom Cards
# ---------------------------------------------------------------------------

class TestCustomCards:
    def test_dimensions_list_response(self, client, mock_api):
        mock_api.get(
            BASE + "design/dimensions",
            json=[
                {"id": 1, "orientation": "landscape", "format": "flat",
                 "open_width": "7", "open_height": "5"},
                {"id": 2, "orientation": "portrait", "format": "folded",
                 "open_width": "5", "open_height": "7"},
            ],
        )

        dims = client.custom_cards.dimensions()

        assert len(dims) == 2
        assert dims[0].id == 1
        assert dims[0].orientation == "landscape"

    def test_dimensions_dict_response(self, client, mock_api):
        mock_api.get(
            BASE + "design/dimensions",
            json={"dimensions": [
                {"id": 1, "orientation": "landscape", "format": "flat",
                 "open_width": "7", "open_height": "5"},
            ]},
        )

        dims = client.custom_cards.dimensions()

        assert len(dims) == 1

    def test_dimensions_filter_by_format(self, client, mock_api):
        mock_api.get(
            BASE + "design/dimensions",
            json=[
                {"id": 1, "orientation": "landscape", "format": "flat",
                 "open_width": "7", "open_height": "5"},
                {"id": 2, "orientation": "portrait", "format": "folded",
                 "open_width": "5", "open_height": "7"},
            ],
        )

        dims = client.custom_cards.dimensions(format="flat")

        assert len(dims) == 1
        assert dims[0].format == "flat"

    def test_dimensions_filter_by_orientation(self, client, mock_api):
        mock_api.get(
            BASE + "design/dimensions",
            json=[
                {"id": 1, "orientation": "landscape", "format": "flat",
                 "open_width": "7", "open_height": "5"},
                {"id": 2, "orientation": "portrait", "format": "folded",
                 "open_width": "5", "open_height": "7"},
            ],
        )

        dims = client.custom_cards.dimensions(orientation="portrait")

        assert len(dims) == 1
        assert dims[0].orientation == "portrait"

    def test_upload_image_by_url(self, client, mock_api):
        mock_api.post(
            BASE + "cards/uploadCustomLogo",
            json={"id": 42, "src": "https://cdn.example.com/img.jpg", "type": "cover"},
        )

        img = client.custom_cards.upload_image(
            url="https://example.com/img.jpg",
            image_type="cover",
        )

        assert img.id == 42
        assert img.image_url == "https://cdn.example.com/img.jpg"
        assert img.image_type == "cover"

    def test_upload_image_requires_url_or_file(self, client, mock_api):
        import pytest

        with pytest.raises(ValueError, match="Provide either url or file_path"):
            client.custom_cards.upload_image()

    def test_upload_image_rejects_both_url_and_file(self, client, mock_api):
        import pytest

        with pytest.raises(ValueError, match="Provide either url or file_path, not both"):
            client.custom_cards.upload_image(url="https://x.com/a.jpg", file_path="/tmp/a.jpg")

    def test_list_images(self, client, mock_api):
        mock_api.get(
            BASE + "cards/listCustomUserImages",
            json={"images": [
                {"id": 1, "src": "https://x.com/a.jpg", "type": "cover"},
                {"id": 2, "src": "https://x.com/b.png", "type": "logo"},
            ]},
        )

        images = client.custom_cards.list_images()

        assert len(images) == 2
        assert images[0].id == 1
        assert images[0].image_url == "https://x.com/a.jpg"

    def test_list_images_with_type_filter(self, client, mock_api):
        mock_api.get(BASE + "cards/listCustomUserImages", json={"images": []})

        client.custom_cards.list_images(image_type="logo")

        assert "type=logo" in mock_api.calls[0].request.url

    def test_list_images_list_response(self, client, mock_api):
        mock_api.get(
            BASE + "cards/listCustomUserImages",
            json=[{"id": 1, "src": "https://x.com/a.jpg"}],
        )

        images = client.custom_cards.list_images()

        assert len(images) == 1

    def test_check_image(self, client, mock_api):
        mock_api.post(
            BASE + "cards/checkUploadedCustomLogo",
            json={"status": "ok"},
        )

        result = client.custom_cards.check_image(image_id=42)

        assert result["status"] == "ok"
        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["image_id"] == 42

    def test_check_image_with_card_id(self, client, mock_api):
        mock_api.post(
            BASE + "cards/checkUploadedCustomLogo",
            json={"status": "ok"},
        )

        client.custom_cards.check_image(image_id=42, card_id=100)

        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["image_id"] == 42
        assert sent["card_id"] == 100

    def test_create_custom_card(self, client, mock_api):
        mock_api.post(
            BASE + "cards/createCustomCard",
            json={"card_id": 999, "category_id": 5},
        )

        card = client.custom_cards.create(
            name="My Card",
            dimension_id="1",
            cover_id=42,
            header_type="logo",
            header_logo_id=10,
            header_logo_size_percent=80,
            qr_code_id=7,
            qr_code_location="footer",
            qr_code_size_percent=100,
        )

        assert card.card_id == 999
        assert card.category_id == 5

        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["name"] == "My Card"
        assert sent["dimension_id"] == "1"
        assert sent["cover_id"] == 42
        assert sent["header_type"] == "logo"
        assert sent["header_logo_id"] == 10
        assert sent["header_logo_size_percent"] == 80
        assert sent["qr_code_id"] == 7
        assert sent["qr_code_location"] == "footer"

    def test_create_custom_card_minimal(self, client, mock_api):
        mock_api.post(
            BASE + "cards/createCustomCard",
            json={"card_id": 100},
        )

        card = client.custom_cards.create(name="Minimal", dimension_id="1")

        assert card.card_id == 100
        sent = json.loads(mock_api.calls[0].request.body)
        assert sent == {"name": "Minimal", "dimension_id": "1"}

    def test_create_with_extra_kwargs(self, client, mock_api):
        mock_api.post(
            BASE + "cards/createCustomCard",
            json={"card_id": 100},
        )

        client.custom_cards.create(
            name="Test", dimension_id="1", custom_param="value",
        )

        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["custom_param"] == "value"

    def test_delete_custom_card(self, client, mock_api):
        mock_api.post(
            BASE + "design/delete",
            json={"status": "ok"},
        )

        result = client.custom_cards.delete(card_id=999)

        assert result["status"] == "ok"
        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["id"] == 999

    def test_delete_image(self, client, mock_api):
        mock_api.post(
            BASE + "cards/deleteCustomLogo",
            json={"status": "ok"},
        )

        result = client.custom_cards.delete_image(image_id=42)

        assert result["status"] == "ok"
        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["image_id"] == 42


# ---------------------------------------------------------------------------
# QR Codes
# ---------------------------------------------------------------------------

class TestQRCodes:
    def test_list(self, client, mock_api):
        mock_api.get(
            BASE + "qrCodes/list",
            json={"list": [
                {"id": 1, "url": "https://example.com", "title": "QR 1"},
                {"id": 2, "url": "https://test.com", "name": "QR 2"},
            ]},
        )

        qr_codes = client.qr_codes.list()

        assert len(qr_codes) == 2
        assert qr_codes[0].id == "1"
        assert qr_codes[0].url == "https://example.com"
        assert qr_codes[1].title == "QR 2"

    def test_list_direct_list_response(self, client, mock_api):
        mock_api.get(
            BASE + "qrCodes/list",
            json=[{"id": 1, "url": "https://example.com"}],
        )

        qr_codes = client.qr_codes.list()

        assert len(qr_codes) == 1

    def test_create(self, client, mock_api):
        mock_api.post(
            BASE + "qrCode/",
            json={"id": 99, "url": "https://example.com", "name": "Test QR"},
        )

        qr = client.qr_codes.create(name="Test QR", url="https://example.com")

        assert qr.id == "99"
        assert qr.url == "https://example.com"

    def test_create_id_only_response(self, client, mock_api):
        """API sometimes returns just {id: ...} without url."""
        mock_api.post(
            BASE + "qrCode/",
            json={"id": 42},
        )

        qr = client.qr_codes.create(name="My QR", url="https://example.com")

        assert qr.id == "42"
        assert qr.url == "https://example.com"
        assert qr.title == "My QR"

    def test_create_with_optional_params(self, client, mock_api):
        mock_api.post(BASE + "qrCode/", json={"id": 1, "url": "https://x.com"})

        client.qr_codes.create(
            name="QR", url="https://x.com",
            icon_id=5, webhook_url="https://hook.com/callback",
        )

        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["name"] == "QR"
        assert sent["url"] == "https://x.com"
        assert sent["icon_id"] == 5
        assert sent["webhook_url"] == "https://hook.com/callback"

    def test_delete(self, client, mock_api):
        mock_api.delete(
            BASE + "qrCode/42/",
            json={"status": "ok"},
        )

        result = client.qr_codes.delete(qr_code_id=42)

        assert result["status"] == "ok"

    def test_frames_dict_response(self, client, mock_api):
        mock_api.get(
            BASE + "qrCode/frames/",
            json={"frames": [
                {"id": 1, "type": "circle", "url": "https://x.com/f1.png"},
                {"id": 2, "type": "square", "url": "https://x.com/f2.png"},
            ]},
        )

        frames = client.qr_codes.frames()

        assert len(frames) == 2
        assert frames[0]["type"] == "circle"

    def test_frames_list_response(self, client, mock_api):
        mock_api.get(
            BASE + "qrCode/frames/",
            json=[{"id": 1, "type": "circle"}],
        )

        frames = client.qr_codes.frames()

        assert len(frames) == 1


# ---------------------------------------------------------------------------
# Prospecting
# ---------------------------------------------------------------------------

class TestProspecting:
    def test_calculate_targets(self, client, mock_api):
        mock_api.post(
            BASE + "prospecting/calculateTargets",
            json={"targets": 150, "area": "Phoenix"},
        )

        result = client.prospecting.calculate_targets(
            zip_code="85001", radius_miles=15,
        )

        assert result["targets"] == 150
        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["zip"] == "85001"
        assert sent["radius"] == 15

    def test_calculate_targets_with_extra_kwargs(self, client, mock_api):
        mock_api.post(
            BASE + "prospecting/calculateTargets",
            json={"targets": 100},
        )

        client.prospecting.calculate_targets(
            zip_code="85001", radius_miles=10, category="residential",
        )

        sent = json.loads(mock_api.calls[0].request.body)
        assert sent["category"] == "residential"
