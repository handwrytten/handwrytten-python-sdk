"""Tests for the CLI address parser and CSV normalizer."""

import pytest

from handwrytten.cli.address_parser import normalize_csv_row, parse_address_string


class TestParseAddressString:
    def test_simple_three_part(self):
        result = parse_address_string("Jane Doe, 123 Main St, Phoenix AZ 85001")

        assert result["firstName"] == "Jane"
        assert result["lastName"] == "Doe"
        assert result["street1"] == "123 Main St"
        assert result["city"] == "Phoenix"
        assert result["state"] == "AZ"
        assert result["zip"] == "85001"

    def test_with_street2(self):
        result = parse_address_string("Jane Doe, 123 Main St, Apt 4B, Phoenix AZ 85001")

        assert result["street1"] == "123 Main St"
        assert result["street2"] == "Apt 4B"
        assert result["city"] == "Phoenix"

    def test_with_company(self):
        result = parse_address_string("Jane Doe, Acme Inc, 123 Main St, Phoenix AZ 85001")

        assert result["company"] == "Acme Inc"
        assert result["street1"] == "123 Main St"
        assert result["city"] == "Phoenix"

    def test_with_company_and_street2(self):
        result = parse_address_string(
            "Jane Doe, Acme Inc, 123 Main St, Suite 200, Phoenix AZ 85001"
        )

        assert result["company"] == "Acme Inc"
        assert result["street1"] == "123 Main St"
        assert result["street2"] == "Suite 200"

    def test_zip_plus_four(self):
        result = parse_address_string("Jane Doe, 123 Main St, Phoenix AZ 85001-1234")

        assert result["zip"] == "85001-1234"

    def test_single_name(self):
        result = parse_address_string("Madonna, 123 Main St, Phoenix AZ 85001")

        assert result["firstName"] == "Madonna"
        assert result["lastName"] == ""

    def test_too_few_parts_raises(self):
        with pytest.raises(ValueError, match="Cannot parse"):
            parse_address_string("Jane Doe, Phoenix")

    def test_no_state_zip_raises(self):
        with pytest.raises(ValueError, match="Cannot find city"):
            parse_address_string("Jane Doe, 123 Main St, Phoenix")

    def test_extra_whitespace(self):
        result = parse_address_string(
            "  Jane   Doe  ,  123 Main St  ,  Phoenix   AZ   85001  "
        )

        assert result["firstName"] == "Jane"
        assert result["lastName"] == "Doe"
        assert result["street1"] == "123 Main St"
        assert result["city"] == "Phoenix"


class TestNormalizeCsvRow:
    def test_api_format_passthrough(self):
        row = {
            "firstName": "Jane",
            "lastName": "Doe",
            "street1": "123 Main St",
            "city": "Phoenix",
            "state": "AZ",
            "zip": "85001",
        }
        result = normalize_csv_row(row)

        assert result["firstName"] == "Jane"
        assert result["zip"] == "85001"

    def test_snake_case_mapping(self):
        row = {
            "first_name": "Jane",
            "last_name": "Doe",
            "street1": "123 Main St",
            "city": "Phoenix",
            "state": "AZ",
            "zip_code": "85001",
        }
        result = normalize_csv_row(row)

        assert result["firstName"] == "Jane"
        assert result["lastName"] == "Doe"
        assert result["zip"] == "85001"

    def test_common_aliases(self):
        row = {
            "fname": "Jane",
            "lname": "Doe",
            "address": "123 Main St",
            "city": "Phoenix",
            "st": "AZ",
            "postal_code": "85001",
            "org": "Acme",
        }
        result = normalize_csv_row(row)

        assert result["firstName"] == "Jane"
        assert result["lastName"] == "Doe"
        assert result["street1"] == "123 Main St"
        assert result["state"] == "AZ"
        assert result["zip"] == "85001"
        assert result["company"] == "Acme"

    def test_empty_values_excluded(self):
        row = {
            "firstName": "Jane",
            "lastName": "Doe",
            "street1": "123 Main",
            "street2": "",
            "city": "Phoenix",
            "state": "AZ",
            "zip": "85001",
        }
        result = normalize_csv_row(row)

        assert "street2" not in result

    def test_whitespace_stripped(self):
        row = {
            "  firstName ": "  Jane  ",
            " lastName": " Doe ",
            "street1": " 123 Main St ",
            "city": " Phoenix ",
            "state": " AZ ",
            "zip": " 85001 ",
        }
        result = normalize_csv_row(row)

        assert result["firstName"] == "Jane"
        assert result["city"] == "Phoenix"
        assert result["zip"] == "85001"
