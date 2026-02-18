"""Address parsing for the CLI.

Parses freeform address strings and CSV rows into the dict format
the Handwrytten API expects.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional


def parse_address_string(addr: str) -> Dict[str, str]:
    """Parse a freeform address string into an API-compatible dict.

    Accepted formats:
        "Jane Doe, 123 Main St, Phoenix AZ 85001"
        "Jane Doe, Acme Inc, 123 Main St, Apt 4B, Phoenix AZ 85001"
        "Jane Doe, 123 Main St, Phoenix, AZ, 85001"

    Returns:
        Dict with keys: firstName, lastName, street1, city, state, zip,
        and optionally street2, company.
    """
    parts = [p.strip() for p in addr.split(",")]

    if len(parts) < 3:
        raise ValueError(
            f"Cannot parse address: expected at least 'Name, Street, City State Zip', got: {addr}"
        )

    result: Dict[str, str] = {}

    # First part is always the name
    name_parts = parts[0].split(None, 1)
    result["firstName"] = name_parts[0]
    result["lastName"] = name_parts[1] if len(name_parts) > 1 else ""

    # Last part should contain city, state, zip — possibly split across commas
    # Try to find state+zip pattern in the remaining parts
    remaining = parts[1:]

    # Rejoin and re-parse the tail to find the city/state/zip
    city_state_zip = _extract_city_state_zip(remaining)

    if city_state_zip:
        result["city"] = city_state_zip["city"]
        result["state"] = city_state_zip["state"]
        result["zip"] = city_state_zip["zip"]

        # Everything between name and city/state/zip is street + optional company
        addr_parts = city_state_zip["preceding"]
        if len(addr_parts) == 1:
            result["street1"] = addr_parts[0]
        elif len(addr_parts) == 2:
            # Could be street + street2 or company + street
            # Heuristic: if first part looks like a street number, it's street1 + street2
            if re.match(r"^\d", addr_parts[0]):
                result["street1"] = addr_parts[0]
                result["street2"] = addr_parts[1]
            else:
                result["company"] = addr_parts[0]
                result["street1"] = addr_parts[1]
        elif len(addr_parts) >= 3:
            result["company"] = addr_parts[0]
            result["street1"] = addr_parts[1]
            result["street2"] = addr_parts[2]
        else:
            raise ValueError(f"Cannot parse street from address: {addr}")
    else:
        raise ValueError(
            f"Cannot find city/state/zip in address: {addr}\n"
            "Expected format: 'Name, Street, City STATE ZIP'"
        )

    return result


def _extract_city_state_zip(parts: list) -> Optional[Dict[str, Any]]:
    """Find the city, state, zip from a list of comma-separated parts.

    Handles:
        ["123 Main St", "Phoenix AZ 85001"]
        ["123 Main St", "Phoenix", "AZ", "85001"]
        ["123 Main St", "Phoenix", "AZ 85001"]
    """
    # Pattern: 2-letter state code followed by 5 or 9 digit zip
    state_zip_re = re.compile(r"([A-Z]{2})\s+(\d{5}(?:-\d{4})?)\s*$")

    # Try from the end, looking for state+zip pattern
    for i in range(len(parts) - 1, -1, -1):
        match = state_zip_re.search(parts[i])
        if match:
            state = match.group(1)
            zip_code = match.group(2)
            city_part = parts[i][: match.start()].strip().rstrip(",").strip()

            # City might be in this same part or the preceding one
            if city_part:
                city = city_part
                preceding = parts[:i]
            elif i > 0:
                city = parts[i - 1].strip()
                preceding = parts[: i - 1]
            else:
                return None

            return {
                "city": city,
                "state": state,
                "zip": zip_code,
                "preceding": preceding,
            }

    # Try: last part is zip, second-to-last is state, third-to-last is city
    if len(parts) >= 3:
        maybe_zip = parts[-1].strip()
        maybe_state = parts[-2].strip()
        if re.match(r"^\d{5}(-\d{4})?$", maybe_zip) and re.match(
            r"^[A-Z]{2}$", maybe_state
        ):
            city = parts[-3].strip()
            preceding = parts[:-3]
            return {
                "city": city,
                "state": maybe_state,
                "zip": maybe_zip,
                "preceding": preceding,
            }

    return None


def normalize_csv_row(row: Dict[str, str]) -> Dict[str, str]:
    """Normalize a CSV row's column names to the API's expected format.

    Handles common variations like first_name → firstName,
    address → street1, zipcode → zip, etc.
    """
    mapping = {
        # firstName
        "first_name": "firstName",
        "firstname": "firstName",
        "first name": "firstName",
        "fname": "firstName",
        # lastName
        "last_name": "lastName",
        "lastname": "lastName",
        "last name": "lastName",
        "lname": "lastName",
        # street1
        "street": "street1",
        "address": "street1",
        "address1": "street1",
        "address_1": "street1",
        "street_1": "street1",
        # street2
        "address2": "street2",
        "address_2": "street2",
        "street_2": "street2",
        "apt": "street2",
        "unit": "street2",
        "suite": "street2",
        # city
        "city": "city",
        # state
        "state": "state",
        "province": "state",
        "st": "state",
        # zip
        "zip": "zip",
        "zipcode": "zip",
        "zip_code": "zip",
        "postal": "zip",
        "postal_code": "zip",
        "postalcode": "zip",
        # company
        "company": "company",
        "organization": "company",
        "org": "company",
        # country
        "country": "country",
        # pass-through API names
        "firstName": "firstName",
        "lastName": "lastName",
        "street1": "street1",
        "street2": "street2",
    }

    result = {}
    for key, value in row.items():
        normalized_key = mapping.get(key.strip().lower(), key.strip())
        if value and value.strip():
            result[normalized_key] = value.strip()

    return result
