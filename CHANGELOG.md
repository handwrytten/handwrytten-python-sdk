# Changelog

All notable changes to the Handwrytten Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2026-04-22

### Added

- **Stamp options** — `client.shipping.stamp_options()` returns available postal stamp options (e.g. First Class vs. Presorted) from `GET /shipping/stampOptions`
- **StampOption model** — new `StampOption` dataclass exported from the package
- `stamp_option_id` parameter on `client.orders.send()` and `client.basket.add_order()` — applies to US mail; ignored for international
- **DeliveryConfirmation constants** — new `DeliveryConfirmation` class exported with `NONE` (0), `CONFIRMATION` (1), `CASS_ONLY` (2) for the widened `delivery_confirmation` parameter

### Changed

- `delivery_confirmation` on `client.orders.send()` and `client.basket.add_order()` now accepts an `int` (`0` none, `1` delivery confirmation, `2` CASS validation only) in addition to `bool`. Booleans remain backward compatible — `False` maps to `0`, `True` maps to `1`.
- `client.orders.send()` now rejects mixing saved-address IDs with full addresses in the `recipient` list. The API treats the two modes differently (top-level `message`/`wishes` for IDs, per-row for full addresses), so the SDK raises `ValueError` up front rather than producing undefined server behavior. Pass either all IDs or all full addresses.
- `client.basket.add_order()` now raises `ValueError` if both `addresses` and `address_ids` are passed, for the same reason.

## [1.2.0] - 2026-02-20

### Added

- **Gift card denominations** — `GiftCard` now includes a `denominations` list with price points (id, nominal value, price)
- **Denomination model** — new `Denomination` dataclass exported from the package
- **Signature model** — new `Signature` dataclass for saved handwriting signatures
- `client.auth.list_signatures()` — list the user's saved handwriting signatures
- `client.custom_cards.get(card_id)` — get details of a custom card
- `client.orders.list_past_baskets(page)` — list previously submitted baskets
- `client.address_book.delete_recipient(address_id, address_ids)` — delete saved recipient addresses (single or batch)
- `client.address_book.delete_sender(address_id, address_ids)` — delete saved sender addresses (single or batch)
- `client.inserts.list(include_historical)` — optional flag to include historical inserts

### Fixed

- Gift card list now correctly extracts items from `gcards` key in API response
- Inserts list now correctly extracts items from `inserts` key in API response

## [1.1.0] - 2026-02-18

### Added

- **Basket management methods** on `client.basket`:
  - `remove(basket_id)` — remove a single item from the basket (`basket/remove`)
  - `clear()` — remove all items from the basket (`basket/clear`)
  - `list()` — list all basket items with totals and pricing (`basket/allNew`)
  - `get_item(basket_id)` — fetch details for a single basket item (`basket/item`)
  - `count()` — get the number of items currently in the basket (`basket/count`)
- `examples/example.py` demonstrating the full basket workflow (inspect, remove, clear)

## [1.0.0] - 2025-02-13

### Added

- **Python SDK** with full Handwrytten API v2 coverage
  - Authentication (`client.auth`)
  - Cards and custom cards (`client.cards`, `client.custom_cards`)
  - Handwriting fonts (`client.fonts`)
  - Orders with single-step and batch sending (`client.orders`)
  - Gift cards, inserts, QR codes (`client.gift_cards`, `client.inserts`, `client.qr_codes`)
  - Address book with countries and states (`client.address_book`)
  - Basket workflow (`client.basket`)
  - Prospecting (`client.prospecting`)
- **CLI tool** (`handwrytten`) with commands:
  - `send` — send notes to single recipients or batch from CSV with `{{field}}` personalization
  - `cards list/get`, `fonts list`, `orders list/get` — browse API resources
  - `gift-cards list`, `inserts list` — browse accessories
  - `address countries/states` — address lookup
  - `account login/whoami/logout` — credential management
- Typed data models with `raw` dict access for unmapped fields
- Automatic retries with exponential backoff for 429s, 5xx, and connection errors
- Idempotency key support on all write operations
- Structured error hierarchy: `AuthenticationError`, `BadRequestError`, `NotFoundError`, `RateLimitError`, `ServerError`
- `--json` output flag on all CLI commands
- `--dry-run` mode for `send` command
- Smart CSV column name normalization (e.g. `first_name` → `firstName`)
- Freeform address string parsing
