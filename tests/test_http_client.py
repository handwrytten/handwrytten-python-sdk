"""Tests for the HTTP client: auth headers, error handling, retries."""

import responses
import pytest

from handwrytten.exceptions import (
    AuthenticationError,
    BadRequestError,
    HandwryttenError,
    NotFoundError,
    RateLimitError,
    ServerError,
)

BASE = "https://api.handwrytten.com/v2/"


class TestAuthentication:
    """Verify the API key is sent correctly."""

    def test_api_key_sent_in_header(self, client, mock_api):
        mock_api.get(BASE + "auth/getUser", json={"id": "1", "email": "a@b.com"})

        client.auth.get_user()

        assert mock_api.calls[0].request.headers["Authorization"] == "test_key_abc123"

    def test_user_agent_sent(self, client, mock_api):
        mock_api.get(BASE + "auth/getUser", json={"id": "1"})

        client.auth.get_user()

        assert "handwrytten-python" in mock_api.calls[0].request.headers["User-Agent"]

    def test_missing_api_key_raises(self):
        with pytest.raises(ValueError, match="API key is required"):
            from handwrytten import Handwrytten
            Handwrytten(api_key="")


class TestErrorHandling:
    """Verify correct exceptions for each HTTP status code."""

    def test_401_raises_authentication_error(self, client, mock_api):
        mock_api.get(
            BASE + "cards/list",
            json={"message": "Invalid token"},
            status=401,
        )

        with pytest.raises(AuthenticationError, match="Invalid token"):
            client.cards.list()

    def test_403_raises_authentication_error(self, client, mock_api):
        mock_api.get(BASE + "cards/list", json={"error": "Forbidden"}, status=403)

        with pytest.raises(AuthenticationError):
            client.cards.list()

    def test_400_raises_bad_request(self, client, mock_api):
        mock_api.post(
            BASE + "orders/placeBasket",
            json={"message": "Missing card_id"},
            status=400,
        )

        with pytest.raises(BadRequestError, match="Missing card_id"):
            client.orders.send(
                card_id="1", font="hwDavid", message="hi",
                recipient={"firstName": "J", "lastName": "D", "street1": "1",
                           "city": "X", "state": "AZ", "zip": "85001"},
            )

    def test_404_raises_not_found(self, client, mock_api):
        mock_api.get(BASE + "cards/get/999", json={"message": "Not found"}, status=404)

        with pytest.raises(NotFoundError):
            client.cards.get("999")

    def test_429_raises_rate_limit(self, client, mock_api):
        mock_api.get(
            BASE + "cards/list",
            json={"message": "Too many requests"},
            status=429,
            headers={"Retry-After": "5"},
        )

        with pytest.raises(RateLimitError) as exc_info:
            client.cards.list()

        assert exc_info.value.retry_after == 5

    def test_500_raises_server_error(self, client, mock_api):
        mock_api.get(BASE + "cards/list", json={"error": "Internal"}, status=500)

        with pytest.raises(ServerError):
            client.cards.list()

    def test_error_preserves_status_code(self, client, mock_api):
        mock_api.get(BASE + "cards/list", json={}, status=422)

        with pytest.raises(BadRequestError) as exc_info:
            client.cards.list()

        assert exc_info.value.status_code == 422

    def test_error_preserves_response_body(self, client, mock_api):
        body = {"errors": ["field1 is required", "field2 is invalid"]}
        mock_api.post(BASE + "orders/placeBasket", json=body, status=400)

        with pytest.raises(BadRequestError) as exc_info:
            client.orders.send(
                card_id="1", font="hwDavid", message="hi",
                recipient={"firstName": "J", "lastName": "D", "street1": "1",
                           "city": "X", "state": "AZ", "zip": "85001"},
            )

        assert exc_info.value.response_body == body


class TestRetries:
    """Verify retry behavior on transient errors."""

    def test_retries_on_500_then_succeeds(self, api_key, mock_api):
        from handwrytten import Handwrytten

        client = Handwrytten(api_key=api_key, max_retries=3)

        # First call: 500, second call: 200
        mock_api.get(BASE + "cards/list", json={"error": "down"}, status=500)
        mock_api.get(BASE + "cards/list", json=[{"id": "1", "title": "Card A"}], status=200)

        cards = client.cards.list()

        assert len(cards) == 1
        assert cards[0].title == "Card A"
        assert len(mock_api.calls) == 2

    def test_no_retry_on_400(self, client, mock_api):
        mock_api.post(
            BASE + "orders/placeBasket",
            json={"message": "Bad input"},
            status=400,
        )

        with pytest.raises(BadRequestError):
            client.orders.send(
                card_id="1", font="hwDavid", message="hi",
                recipient={"firstName": "J", "lastName": "D", "street1": "1",
                           "city": "X", "state": "AZ", "zip": "85001"},
            )

        # Should NOT retry 400s
        assert len(mock_api.calls) == 1


class TestClientInit:
    """Verify Handwrytten client initialization."""

    def test_repr_masks_api_key(self):
        from handwrytten import Handwrytten

        client = Handwrytten(api_key="abcdefghijklmnop")
        r = repr(client)
        assert "abcdefgh..." in r
        assert "ijklmnop" not in r

    def test_all_resource_namespaces(self):
        from handwrytten import Handwrytten

        client = Handwrytten(api_key="test_key_123")
        assert hasattr(client, "auth")
        assert hasattr(client, "cards")
        assert hasattr(client, "custom_cards")
        assert hasattr(client, "fonts")
        assert hasattr(client, "gift_cards")
        assert hasattr(client, "inserts")
        assert hasattr(client, "qr_codes")
        assert hasattr(client, "address_book")
        assert hasattr(client, "basket")
        assert hasattr(client, "orders")
        assert hasattr(client, "prospecting")


class TestHttpMethods:
    """Verify PUT and DELETE HTTP methods work."""

    def test_put_method(self, client, mock_api):
        mock_api.put(
            BASE + "profile/updateRecipient",
            json={"address": {"id": 123}},
        )

        client.address_book.update_recipient(address_id=123, city="Scottsdale")

        assert mock_api.calls[0].request.method == "PUT"

    def test_delete_method(self, client, mock_api):
        mock_api.delete(
            BASE + "qrCode/42/",
            json={"status": "ok"},
        )

        result = client.qr_codes.delete(qr_code_id=42)

        assert mock_api.calls[0].request.method == "DELETE"
        assert result["status"] == "ok"

    def test_idempotency_key_header(self, client, mock_api):
        mock_api.post(
            BASE + "orders/placeBasket",
            json={"order_id": "ord_123"},
        )

        client._http.post(
            "orders/placeBasket",
            json_body={"card_id": 100},
            idempotency_key="my-unique-key-123",
        )

        assert mock_api.calls[0].request.headers["Idempotency-Key"] == "my-unique-key-123"
