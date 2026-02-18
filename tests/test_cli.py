"""Tests for the CLI send command and other CLI subcommands."""

import json
import os
import tempfile

import responses
from click.testing import CliRunner

from handwrytten.cli import cli

BASE = "https://api.handwrytten.com/v2/"
API_KEY = "test_cli_key"


def _mock_order_flow(place_json=None, send_json=None):
    """Register both placeBasket and basket/send mocks."""
    responses.post(
        BASE + "orders/placeBasket",
        json=place_json or {"order_id": "ord_cli_1"},
    )
    responses.post(
        BASE + "basket/send",
        json=send_json or {"id": "ord_cli_1", "status": "processing"},
    )


@responses.activate
def test_send_single_recipient():
    _mock_order_flow()

    runner = CliRunner()
    result = runner.invoke(cli, [
        "--api-key", API_KEY,
        "send",
        "--card", "100",
        "--font", "10",
        "--message", "Thank you!",
        "--to", "Jane Doe, 123 Main St, Phoenix AZ 85001",
    ])

    assert result.exit_code == 0
    assert "ord_cli_1" in result.output

    # Verify the placeBasket payload
    sent = json.loads(responses.calls[0].request.body)
    assert sent["card_id"] == 100
    assert sent["font"] == "10"
    assert sent["addresses"][0]["to_first_name"] == "Jane"


@responses.activate
def test_send_dry_run():
    runner = CliRunner()
    result = runner.invoke(cli, [
        "--api-key", API_KEY,
        "send",
        "--card", "100",
        "--font", "10",
        "--message", "Thank you!",
        "--to", "Jane Doe, 123 Main St, Phoenix AZ 85001",
        "--dry-run",
    ])

    assert result.exit_code == 0
    assert "DRY RUN" in result.output
    assert "Jane Doe" in result.output
    # No API calls should have been made
    assert len(responses.calls) == 0


@responses.activate
def test_send_from_csv():
    # Each CSV row triggers a separate orders.send() call (placeBasket + basket/send)
    _mock_order_flow(
        send_json={"id": "ord_csv_1", "status": "processing"},
    )
    _mock_order_flow(
        send_json={"id": "ord_csv_2", "status": "processing"},
    )

    csv_content = (
        "firstName,lastName,street1,city,state,zip\n"
        "Jane,Doe,123 Main St,Phoenix,AZ,85001\n"
        "John,Smith,456 Oak Ave,Scottsdale,AZ,85251\n"
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        csv_path = f.name

    try:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "--api-key", API_KEY,
            "send",
            "--card", "100",
            "--font", "10",
            "--message", "Hi {{firstName}}!",
            "--from-csv", csv_path,
        ])

        assert result.exit_code == 0
        assert "ord_csv_1" in result.output
        assert "ord_csv_2" in result.output
        # 2 recipients = 2x (placeBasket + basket/send) = 4 calls
        assert len(responses.calls) == 4

        # Verify personalization in first placeBasket call
        body1 = json.loads(responses.calls[0].request.body)
        assert body1["addresses"][0]["message"] == "Hi Jane!"
        # Verify personalization in second placeBasket call
        body2 = json.loads(responses.calls[2].request.body)
        assert body2["addresses"][0]["message"] == "Hi John!"
    finally:
        os.unlink(csv_path)


@responses.activate
def test_send_json_output():
    _mock_order_flow(
        send_json={"id": "ord_json_1", "status": "processing"},
    )

    runner = CliRunner()
    result = runner.invoke(cli, [
        "--api-key", API_KEY,
        "--json",
        "send",
        "--card", "100",
        "--font", "10",
        "--message", "Thanks!",
        "--to", "Jane Doe, 123 Main St, Phoenix AZ 85001",
    ])

    assert result.exit_code == 0
    # The output may contain an info line on stderr mixed in; find the JSON array
    output = result.output
    json_start = output.index("[")
    parsed = json.loads(output[json_start:])
    assert isinstance(parsed, list)
    assert parsed[0]["id"] == "ord_json_1"


def test_send_missing_message():
    runner = CliRunner()
    result = runner.invoke(cli, [
        "--api-key", API_KEY,
        "send",
        "--card", "100",
        "--font", "10",
        "--to", "Jane Doe, 123 Main St, Phoenix AZ 85001",
    ], input="")

    assert result.exit_code != 0


def test_send_missing_recipient():
    runner = CliRunner()
    result = runner.invoke(cli, [
        "--api-key", API_KEY,
        "send",
        "--card", "100",
        "--font", "10",
        "--message", "Thanks!",
    ])

    assert result.exit_code != 0


@responses.activate
def test_send_message_from_file():
    _mock_order_flow(
        send_json={"id": "ord_file_1", "status": "processing"},
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Hello from a file!")
        msg_path = f.name

    try:
        runner = CliRunner()
        result = runner.invoke(cli, [
            "--api-key", API_KEY,
            "send",
            "--card", "100",
            "--font", "10",
            "--message-file", msg_path,
            "--to", "Jane Doe, 123 Main St, Phoenix AZ 85001",
        ])

        assert result.exit_code == 0
        body = json.loads(responses.calls[0].request.body)
        assert body["addresses"][0]["message"] == "Hello from a file!"
    finally:
        os.unlink(msg_path)


@responses.activate
def test_send_with_gift_card():
    _mock_order_flow()

    runner = CliRunner()
    result = runner.invoke(cli, [
        "--api-key", API_KEY,
        "send",
        "--card", "100",
        "--font", "10",
        "--message", "Thanks!",
        "--to", "Jane Doe, 123 Main St, Phoenix AZ 85001",
        "--gift-card", "50",
    ])

    assert result.exit_code == 0
    body = json.loads(responses.calls[0].request.body)
    assert body["denomination_id"] == 50


@responses.activate
def test_send_with_insert():
    _mock_order_flow()

    runner = CliRunner()
    result = runner.invoke(cli, [
        "--api-key", API_KEY,
        "send",
        "--card", "100",
        "--font", "10",
        "--message", "Thanks!",
        "--to", "Jane Doe, 123 Main St, Phoenix AZ 85001",
        "--insert", "5",
    ])

    assert result.exit_code == 0
    body = json.loads(responses.calls[0].request.body)
    assert body["insert_id"] == 5


@responses.activate
def test_send_with_return_address():
    _mock_order_flow()

    runner = CliRunner()
    result = runner.invoke(cli, [
        "--api-key", API_KEY,
        "send",
        "--card", "100",
        "--font", "10",
        "--message", "Thanks!",
        "--to", "Jane Doe, 123 Main St, Phoenix AZ 85001",
        "--from", "David Wachs, 3433 E Main Ave, Phoenix AZ 85018",
    ])

    assert result.exit_code == 0
    body = json.loads(responses.calls[0].request.body)
    addr = body["addresses"][0]
    assert addr["from_first_name"] == "David"
    assert addr["from_last_name"] == "Wachs"


# ---------------------------------------------------------------------------
# Non-send CLI commands
# ---------------------------------------------------------------------------

@responses.activate
def test_cards_list_cli():
    responses.get(
        BASE + "cards/list",
        json=[
            {"id": 1, "title": "Thank You"},
            {"id": 2, "title": "Birthday"},
        ],
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["--api-key", API_KEY, "cards", "list"])

    assert result.exit_code == 0
    assert "Thank You" in result.output
    assert "Birthday" in result.output


@responses.activate
def test_fonts_list_cli():
    responses.get(
        BASE + "fonts/list",
        json=[{"id": 10, "name": "Classic"}],
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["--api-key", API_KEY, "fonts", "list"])

    assert result.exit_code == 0
    assert "Classic" in result.output


@responses.activate
def test_orders_get_cli():
    responses.get(
        BASE + "orders/get/ord_test",
        json={"id": "ord_test", "status": "delivered", "trackingNumber": "TRK999"},
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["--api-key", API_KEY, "orders", "get", "ord_test"])

    assert result.exit_code == 0
    assert "delivered" in result.output
    assert "TRK999" in result.output


@responses.activate
def test_orders_list_cli():
    responses.get(
        BASE + "orders/list",
        json=[
            {"id": "ord_1", "status": "processing"},
            {"id": "ord_2", "status": "delivered"},
        ],
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["--api-key", API_KEY, "orders", "list"])

    assert result.exit_code == 0
    assert "ord_1" in result.output
    assert "ord_2" in result.output


@responses.activate
def test_gift_cards_list_cli():
    responses.get(
        BASE + "giftCards/list",
        json=[{"id": 1, "title": "$25 Amazon", "amount": 25.0}],
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["--api-key", API_KEY, "gift-cards", "list"])

    assert result.exit_code == 0
    assert "$25 Amazon" in result.output


@responses.activate
def test_inserts_list_cli():
    responses.get(
        BASE + "inserts/list",
        json=[{"id": 1, "title": "Business Card"}],
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["--api-key", API_KEY, "inserts", "list"])

    assert result.exit_code == 0
    assert "Business Card" in result.output


@responses.activate
def test_account_whoami_cli():
    responses.get(
        BASE + "auth/getUser",
        json={"id": "u1", "email": "test@example.com", "firstName": "Jane",
              "lastName": "Doe", "credits": 42.5},
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["--api-key", API_KEY, "account", "whoami"])

    assert result.exit_code == 0
    assert "test@example.com" in result.output


@responses.activate
def test_address_countries_cli():
    responses.get(
        BASE + "countries/list",
        json=[{"code": "US", "name": "United States"}, {"code": "CA", "name": "Canada"}],
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["--api-key", API_KEY, "address", "countries"])

    assert result.exit_code == 0
    assert "United States" in result.output


@responses.activate
def test_address_states_cli():
    responses.get(
        BASE + "states/list",
        json=[{"abbreviation": "AZ", "name": "Arizona"}],
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["--api-key", API_KEY, "address", "states"])

    assert result.exit_code == 0
    assert "Arizona" in result.output
