# Changelog

All notable changes to the Handwrytten Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
