"""Tests for all data models in handwrytten.models."""

from handwrytten.models import (
    Card,
    Country,
    CustomCard,
    CustomImage,
    Denomination,
    Dimension,
    Font,
    GiftCard,
    Insert,
    Order,
    QRCode,
    QRCodeLocation,
    Recipient,
    SavedAddress,
    Sender,
    Signature,
    State,
    User,
    ZoneType,
)


class TestUser:
    def test_from_dict_basic(self):
        u = User.from_dict({"id": 123, "email": "a@b.com"})
        assert u.id == "123"
        assert u.email == "a@b.com"

    def test_from_dict_camel_case(self):
        u = User.from_dict({"id": 1, "firstName": "Jane", "lastName": "Doe"})
        assert u.first_name == "Jane"
        assert u.last_name == "Doe"

    def test_from_dict_snake_case(self):
        u = User.from_dict({"id": 1, "first_name": "Jane", "last_name": "Doe"})
        assert u.first_name == "Jane"
        assert u.last_name == "Doe"

    def test_from_dict_uid_fallback(self):
        u = User.from_dict({"uid": "abc"})
        assert u.id == "abc"

    def test_from_dict_credits(self):
        u = User.from_dict({"id": 1, "credits": 42.5})
        assert u.credits == 42.5

    def test_raw_preserved(self):
        data = {"id": 1, "email": "a@b.com", "extra_field": "hello"}
        u = User.from_dict(data)
        assert u.raw == data
        assert u.raw["extra_field"] == "hello"

    def test_defaults(self):
        u = User.from_dict({})
        assert u.id == ""
        assert u.email is None
        assert u.first_name is None


class TestCard:
    def test_from_dict_basic(self):
        c = Card.from_dict({"id": 42, "title": "Thank You"})
        assert c.id == "42"
        assert c.title == "Thank You"

    def test_image_url_from_cover(self):
        c = Card.from_dict({"id": 1, "title": "X", "cover": "https://img.com/x.jpg"})
        assert c.image_url == "https://img.com/x.jpg"
        assert c.cover == "https://img.com/x.jpg"

    def test_image_url_from_image(self):
        c = Card.from_dict({"id": 1, "title": "X", "image": "https://img.com/x.jpg"})
        assert c.image_url == "https://img.com/x.jpg"

    def test_category_from_product_type(self):
        c = Card.from_dict({"id": 1, "title": "X", "product_type": "greeting"})
        assert c.category == "greeting"

    def test_title_from_name_fallback(self):
        c = Card.from_dict({"id": 1, "name": "Fallback Name"})
        assert c.title == "Fallback Name"

    def test_raw_preserved(self):
        data = {"id": 1, "title": "X", "custom_field": 99}
        c = Card.from_dict(data)
        assert c.raw["custom_field"] == 99


class TestFont:
    def test_from_dict_basic(self):
        f = Font.from_dict({"id": 10, "name": "Classic", "preview_url": "https://x.com/c.jpg"})
        assert f.id == "10"
        assert f.name == "Classic"
        assert f.label == "Classic"
        assert f.preview_url == "https://x.com/c.jpg"

    def test_label_fallback(self):
        f = Font.from_dict({"id": 1, "name": "Foo", "label": "Bar"})
        assert f.name == "Foo"
        assert f.label == "Bar"

    def test_preview_from_image(self):
        f = Font.from_dict({"id": 1, "name": "X", "image": "https://x.com/i.jpg"})
        assert f.preview_url == "https://x.com/i.jpg"

    def test_preview_from_preview(self):
        f = Font.from_dict({"id": 1, "name": "X", "preview": "https://x.com/p.jpg"})
        assert f.preview_url == "https://x.com/p.jpg"


class TestDenomination:
    def test_from_dict_basic(self):
        d = Denomination.from_dict({"id": 10, "nominal": 25.0, "price": 27.5})
        assert d.id == 10
        assert d.nominal == 25.0
        assert d.price == 27.5

    def test_defaults(self):
        d = Denomination.from_dict({})
        assert d.id == 0
        assert d.nominal == 0.0
        assert d.price == 0.0

    def test_raw_preserved(self):
        data = {"id": 1, "nominal": 10, "price": 12, "extra": True}
        d = Denomination.from_dict(data)
        assert d.raw["extra"] is True


class TestGiftCard:
    def test_from_dict_basic(self):
        gc = GiftCard.from_dict({"id": 5, "title": "$25 Amazon", "amount": 25.0})
        assert gc.id == "5"
        assert gc.title == "$25 Amazon"
        assert gc.amount == 25.0

    def test_amount_from_value(self):
        gc = GiftCard.from_dict({"id": 1, "title": "X", "value": 50.0})
        assert gc.amount == 50.0

    def test_image_url(self):
        gc = GiftCard.from_dict({"id": 1, "title": "X", "image_url": "https://x.com/gc.jpg"})
        assert gc.image_url == "https://x.com/gc.jpg"

    def test_with_denominations(self):
        gc = GiftCard.from_dict({
            "id": 5,
            "title": "Amazon",
            "denominations": [
                {"id": 1, "nominal": 25.0, "price": 27.5},
                {"id": 2, "nominal": 50.0, "price": 55.0},
            ],
        })
        assert len(gc.denominations) == 2
        assert gc.denominations[0].nominal == 25.0
        assert gc.denominations[1].price == 55.0

    def test_empty_denominations(self):
        gc = GiftCard.from_dict({"id": 1, "title": "X"})
        assert gc.denominations == []

    def test_non_list_denominations_ignored(self):
        gc = GiftCard.from_dict({"id": 1, "title": "X", "denominations": "invalid"})
        assert gc.denominations == []


class TestInsert:
    def test_from_dict_basic(self):
        i = Insert.from_dict({"id": 3, "title": "Business Card"})
        assert i.id == "3"
        assert i.title == "Business Card"

    def test_title_from_name(self):
        i = Insert.from_dict({"id": 1, "name": "Flyer"})
        assert i.title == "Flyer"

    def test_image_url(self):
        i = Insert.from_dict({"id": 1, "title": "X", "image": "https://x.com/i.jpg"})
        assert i.image_url == "https://x.com/i.jpg"


class TestQRCode:
    def test_from_dict_basic(self):
        qr = QRCode.from_dict({"id": 7, "url": "https://example.com", "title": "My QR"})
        assert qr.id == "7"
        assert qr.url == "https://example.com"
        assert qr.title == "My QR"

    def test_title_from_name(self):
        qr = QRCode.from_dict({"id": 1, "name": "Test QR"})
        assert qr.title == "Test QR"

    def test_raw_preserved(self):
        data = {"id": 1, "url": "https://x.com", "extra": True}
        qr = QRCode.from_dict(data)
        assert qr.raw["extra"] is True


class TestRecipient:
    def test_to_dict_basic(self):
        r = Recipient(
            first_name="Jane", last_name="Doe",
            street1="123 Main St", city="Phoenix", state="AZ", zip="85001",
        )
        d = r.to_dict()
        assert d["firstName"] == "Jane"
        assert d["lastName"] == "Doe"
        assert d["street1"] == "123 Main St"
        assert d["city"] == "Phoenix"
        assert d["state"] == "AZ"
        assert d["zip"] == "85001"
        assert d["country"] == "US"

    def test_to_dict_with_optional_fields(self):
        r = Recipient(
            first_name="Jane", last_name="Doe",
            street1="123 Main", city="X", state="AZ", zip="85001",
            street2="Apt 4", company="Acme Inc",
        )
        d = r.to_dict()
        assert d["street2"] == "Apt 4"
        assert d["company"] == "Acme Inc"

    def test_to_dict_omits_empty_optional(self):
        r = Recipient(
            first_name="Jane", last_name="Doe",
            street1="123 Main", city="X", state="AZ", zip="85001",
        )
        d = r.to_dict()
        assert "street2" not in d
        assert "company" not in d

    def test_custom_country(self):
        r = Recipient(
            first_name="J", last_name="D",
            street1="1", city="X", state="ON", zip="K1A0A9",
            country="CA",
        )
        assert r.to_dict()["country"] == "CA"


class TestSender:
    def test_to_dict_basic(self):
        s = Sender(
            first_name="David", last_name="Wachs",
            street1="100 S Mill Ave", city="Tempe", state="AZ", zip="85281",
        )
        d = s.to_dict()
        assert d["firstName"] == "David"
        assert d["lastName"] == "Wachs"
        assert d["street1"] == "100 S Mill Ave"
        assert d["country"] == "US"

    def test_to_dict_with_optional_fields(self):
        s = Sender(
            first_name="D", last_name="W",
            street1="1", city="X", state="AZ", zip="85001",
            street2="Suite 200", company="Handwrytten",
        )
        d = s.to_dict()
        assert d["street2"] == "Suite 200"
        assert d["company"] == "Handwrytten"


class TestOrder:
    def test_from_dict_basic(self):
        o = Order.from_dict({"id": "ord_abc", "status": "processing"})
        assert o.id == "ord_abc"
        assert o.status == "processing"

    def test_from_dict_tracking(self):
        o = Order.from_dict({"id": "1", "trackingNumber": "TRK123"})
        assert o.tracking_number == "TRK123"

    def test_from_dict_snake_tracking(self):
        o = Order.from_dict({"id": "1", "tracking_number": "TRK456"})
        assert o.tracking_number == "TRK456"

    def test_from_dict_created_at(self):
        o = Order.from_dict({"id": "1", "createdAt": "2025-01-15T10:30:00Z"})
        assert o.created_at == "2025-01-15T10:30:00Z"

    def test_from_dict_order_id_fallback(self):
        o = Order.from_dict({"order_id": "ord_999"})
        assert o.id == "ord_999"

    def test_card_id_and_font_id(self):
        o = Order.from_dict({"id": "1", "card_id": 42, "font_id": 10})
        assert o.card_id == "42"
        assert o.font_id == "10"

    def test_none_card_id(self):
        o = Order.from_dict({"id": "1"})
        assert o.card_id is None
        assert o.font_id is None


class TestDimension:
    def test_from_dict_basic(self):
        d = Dimension.from_dict({
            "id": 5,
            "orientation": "landscape",
            "format": "flat",
            "open_width": "7",
            "open_height": "5",
            "name": "7x5 Flat",
        })
        assert d.id == 5
        assert d.orientation == "landscape"
        assert d.format == "flat"
        assert d.open_width == "7"
        assert d.open_height == "5"
        assert d.name == "7x5 Flat"

    def test_str(self):
        d = Dimension.from_dict({
            "id": 1,
            "orientation": "portrait",
            "format": "folded",
            "open_width": "5",
            "open_height": "7",
        })
        assert str(d) == "5x7 folded (portrait)"

    def test_raw_preserved(self):
        data = {"id": 1, "orientation": "x", "format": "y", "open_width": "1", "open_height": "2", "extra": True}
        d = Dimension.from_dict(data)
        assert d.raw["extra"] is True


class TestCustomImage:
    def test_from_dict_basic(self):
        img = CustomImage.from_dict({"id": 99, "src": "https://x.com/img.jpg", "type": "cover"})
        assert img.id == 99
        assert img.image_url == "https://x.com/img.jpg"
        assert img.image_type == "cover"

    def test_url_from_image_url(self):
        img = CustomImage.from_dict({"id": 1, "image_url": "https://x.com/a.jpg"})
        assert img.image_url == "https://x.com/a.jpg"

    def test_url_from_url(self):
        img = CustomImage.from_dict({"id": 1, "url": "https://x.com/b.jpg"})
        assert img.image_url == "https://x.com/b.jpg"


class TestCustomCard:
    def test_from_dict_basic(self):
        cc = CustomCard.from_dict({"card_id": 42, "category_id": 3})
        assert cc.card_id == 42
        assert cc.category_id == 3

    def test_from_dict_id_fallback(self):
        cc = CustomCard.from_dict({"id": 100})
        assert cc.card_id == 100

    def test_no_category_id(self):
        cc = CustomCard.from_dict({"card_id": 1})
        assert cc.category_id is None


class TestSavedAddress:
    def test_from_dict_basic(self):
        sa = SavedAddress.from_dict({
            "id": 123,
            "first_name": "Jane",
            "last_name": "Doe",
            "address1": "123 Main St",
            "address2": "Apt 4",
            "city": "Phoenix",
            "state": "AZ",
            "zip": "85001",
            "business_name": "Acme",
            "country": "US",
        })
        assert sa.id == 123
        assert sa.first_name == "Jane"
        assert sa.last_name == "Doe"
        assert sa.street1 == "123 Main St"
        assert sa.street2 == "Apt 4"
        assert sa.city == "Phoenix"
        assert sa.state == "AZ"
        assert sa.zip == "85001"
        assert sa.company == "Acme"
        assert sa.country == "US"

    def test_state_from_states_key(self):
        sa = SavedAddress.from_dict({"id": 1, "states": "CA"})
        assert sa.state == "CA"

    def test_str(self):
        sa = SavedAddress.from_dict({
            "id": 1,
            "first_name": "Jane",
            "last_name": "Doe",
            "address1": "123 Main",
            "city": "Phoenix",
            "state": "AZ",
            "zip": "85001",
        })
        assert str(sa) == "Jane Doe, 123 Main, Phoenix, AZ 85001"


class TestSignature:
    def test_from_dict_basic(self):
        s = Signature.from_dict({"id": 7, "preview": "https://x.com/sig.png"})
        assert s.id == 7
        assert s.preview == "https://x.com/sig.png"

    def test_defaults(self):
        s = Signature.from_dict({})
        assert s.id == 0
        assert s.preview is None

    def test_raw_preserved(self):
        data = {"id": 1, "preview": "x", "extra": True}
        s = Signature.from_dict(data)
        assert s.raw["extra"] is True


class TestCountry:
    def test_from_dict_basic(self):
        c = Country.from_dict({"code": "US", "name": "United States"})
        assert c.code == "US"
        assert c.name == "United States"

    def test_code_from_id(self):
        c = Country.from_dict({"id": "CA", "name": "Canada"})
        assert c.code == "CA"


class TestState:
    def test_from_dict_basic(self):
        s = State.from_dict({"code": "AZ", "name": "Arizona"})
        assert s.code == "AZ"
        assert s.name == "Arizona"

    def test_code_from_abbreviation(self):
        s = State.from_dict({"abbreviation": "CA", "name": "California"})
        assert s.code == "CA"


class TestZoneType:
    def test_constants(self):
        assert ZoneType.TEXT == "text"
        assert ZoneType.LOGO == "logo"
        assert ZoneType.COVER == "cover"


class TestQRCodeLocation:
    def test_constants(self):
        assert QRCodeLocation.HEADER == "header"
        assert QRCodeLocation.FOOTER == "footer"
        assert QRCodeLocation.MAIN == "main"
