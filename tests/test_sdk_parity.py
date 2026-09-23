"""Regression fixtures shared with the JavaScript SDK. No production writes."""
import copy
import json
from pathlib import Path

import pytest

from handwrytten import Handwrytten, HandwryttenError, Country
from handwrytten import DeliveryConfirmation, GiftCard, User

BASE = "https://api.handwrytten.com/v2/"
FIXTURE = json.loads((Path(__file__).parent / "fixtures/sdk-parity.json").read_text())


def test_shared_resource_methods(client):
    import inspect
    found = {
        type(resource).__name__: sorted(name for name, _ in inspect.getmembers(resource, inspect.ismethod)
                                       if not name.startswith("_"))
        for resource in vars(client).values() if type(resource).__name__.endswith("Resource")
    }
    assert found == {name: sorted(methods) for name, methods in FIXTURE["resource_methods"].items()}


@pytest.mark.parametrize("case", FIXTURE["numeric_models"])
def test_numeric_models(case):
    model = {"User": User, "GiftCard": GiftCard}[case["model"]]
    parsed = model.from_dict(case["raw"])
    assert getattr(parsed, case["field"]) == case["expected"]
    assert parsed.raw == case["raw"]


def test_delivery_confirmation_aliases():
    assert DeliveryConfirmation.CONFIRMATION == DeliveryConfirmation.DELIVERY_CONFIRMATION == 1
    assert DeliveryConfirmation.CASS_ONLY == DeliveryConfirmation.CASS_VALIDATION == 2


@pytest.mark.parametrize("image_type", ["logo", "cover"])
def test_file_upload_retry_preserves_bytes_and_type(mock_api, tmp_path, image_type):
    client = Handwrytten("test-key", max_retries=2)
    path = tmp_path / "image.png"
    path.write_bytes(b"image-content")
    mock_api.post(BASE + "cards/uploadCustomLogo", status=500, json={"message": "retry"})
    mock_api.post(BASE + "cards/uploadCustomLogo", json={"id": 7})
    result = client.custom_cards.upload_image(file_path=str(path), image_type=image_type)
    assert result.id == 7
    assert len(mock_api.calls) == 2
    for call in mock_api.calls:
        assert b"image-content" in call.request.body
        assert b'filename="image.png"' in call.request.body
        assert image_type.encode() in call.request.body
        assert call.request.headers["Content-Type"].startswith("multipart/form-data; boundary=")


@pytest.mark.parametrize("oauth", [False, True])
def test_card_dimensions_and_auth(mock_api, oauth):
    raw = FIXTURE["card"]
    mock_api.get(BASE + "cards/view?card_id=100", json={"status": "ok", "card": raw})
    client = Handwrytten(access_token="test-token") if oauth else Handwrytten("test-key")
    card = client.cards.get("100")
    assert card.id == "100"
    assert card.raw == raw
    assert card.raw["preview_margin_top"] == 0
    assert mock_api.calls[0].request.headers["Authorization"] == ("Bearer test-token" if oauth else "test-key")


@pytest.mark.parametrize("body", [{}, {"card": None}, {"card": []}, {"card": {}}, {"card": {"id": 101}}])
def test_invalid_card_response(client, mock_api, body):
    mock_api.get(BASE + "cards/view?card_id=100", json=body)
    with pytest.raises(HandwryttenError, match="no matching card"):
        client.cards.get("100")


@pytest.mark.parametrize("status", [400, 401, 404])
def test_card_backend_errors(client, mock_api, status):
    mock_api.get(BASE + "cards/view?card_id=100", status=status, json={"message": "Lookup failed"})
    with pytest.raises(HandwryttenError) as error:
        client.cards.get("100")
    assert error.value.status_code == status


@pytest.mark.parametrize("key", [None, "categories", "results"])
def test_categories_preserve_dictionary_interface(client, mock_api, key):
    items = [FIXTURE["category"]]
    mock_api.get(BASE + "categories/list", json={key: items} if key else items)
    assert client.cards.categories() == items


@pytest.mark.parametrize("key", [None, "countries", "results"])
def test_country_enrichment(client, mock_api, key):
    items = [FIXTURE["country"]]
    mock_api.get(BASE + "countries/list", json={key: items} if key else items)
    country = client.address_book.countries()[0]
    assert (country.id, country.code, country.delivery_cost) == (1, "US", 0.78)
    assert country.aliases == ["USA", "U.S.A.", "US"]
    assert country.raw == FIXTURE["country"]
    assert Country.from_dict({"id": 99}).code == ""
    assert Country.from_dict({}).delivery_cost == 0
    assert Country.from_dict({"delivery_cost": "invalid"}).delivery_cost == 0
    # Existing positional constructor arguments retain their meaning.
    assert Country("US", "United States", {"legacy": True}).raw == {"legacy": True}


@pytest.mark.parametrize("key", [None, "stamp_options", "stampOptions", "options", "results"])
def test_stamp_envelopes(client, mock_api, key):
    items = [FIXTURE["stamp"]]
    mock_api.get(BASE + "shipping/stampOptions", json={key: items} if key else items)
    stamp = client.shipping.stamp_options()[0]
    assert (stamp.id, stamp.name, stamp.price) == (2, "Presorted", 0.5)


@pytest.mark.parametrize("value,expected", [(False, 0), (True, 1), (0, 0), (1, 1), (2, 2)])
def test_delivery_confirmation(client, mock_api, value, expected):
    mock_api.post(BASE + "orders/placeBasket", json={"ok": True})
    client.basket.add_order(card_id="100", delivery_confirmation=value)
    body = json.loads(mock_api.calls[0].request.body)
    assert body["delivery_confirmation"] == expected
    assert type(body["delivery_confirmation"]) is int


def test_saved_recipient_payload(client, mock_api):
    mock_api.post(BASE + "orders/placeBasket", json={"ok": True})
    mock_api.post(BASE + "basket/send", json={"ok": True})
    client.orders.send(card_id="100", font="hwDavid", recipient=[1, 2], sender=99,
                       message="Hello", wishes="Best", delivery_confirmation=2, stamp_option_id=2)
    assert json.loads(mock_api.calls[0].request.body) == FIXTURE["saved_order"]


def test_return_address_rows_without_mutation(client, mock_api):
    rows = [copy.deepcopy(FIXTURE["inline"]), {**FIXTURE["inline"], "return_address_id": 77}]
    original = copy.deepcopy(rows)
    mock_api.post(BASE + "orders/placeBasket", json={"ok": True})
    client.basket.add_order(card_id="100", addresses=rows, return_address_id=99)
    payload = json.loads(mock_api.calls[0].request.body)
    assert [r["return_address_id"] for r in payload["addresses"]] == [99, 77]
    assert rows == original


@pytest.mark.parametrize("rows,ids", [([], []), ([FIXTURE["inline"]], [1])])
def test_mixed_basket_modes_fail_before_request(client, mock_api, rows, ids):
    with pytest.raises(ValueError, match="not both"):
        client.basket.add_order(card_id="100", addresses=rows, address_ids=ids)
    assert len(mock_api.calls) == 0


def test_qr_short_response_keeps_raw(client, mock_api):
    mock_api.post(BASE + "qrCode/", json={"id": 12, "status": "ok"})
    qr = client.qr_codes.create(name="Test", url="https://example.com")
    assert qr.raw == {"id": 12, "status": "ok"}

@pytest.mark.parametrize("code,expected", [("US", "AZ"), ("ca", "ON"), ("XX", None)])
def test_states_select_country(client, mock_api, code, expected):
    mock_api.get(BASE + "countries/list", json={"countries": [FIXTURE["country"],
        {"id": 2, "ups_code": "CA", "states": [{"short_name": "ON", "name": "Ontario"}]}]})
    states = client.address_book.states(code)
    assert ([s.code for s in states]) == ([expected] if expected else [])


def test_non_json_error_preserved(client, mock_api):
    mock_api.get(BASE + "cards/view?card_id=100", body="Invalid card", status=400)
    with pytest.raises(HandwryttenError) as error:
        client.cards.get("100")
    assert error.value.response_body == "Invalid card"


@pytest.mark.parametrize("recipient", [True, False, None, "invalid"])
def test_invalid_scalar_recipient(client, mock_api, recipient):
    with pytest.raises(TypeError):
        client.orders.send(card_id="100", font="hwDavid", recipient=recipient)
    assert len(mock_api.calls) == 0
