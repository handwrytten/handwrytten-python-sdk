# JavaScript / Python SDK parity review

Reviewed the local JavaScript SDK through `7ba25b9` and Python SDK through `311b7f9`, including both commit histories, shared resource methods and routes, request serialization, response models, authentication, and HTTP error handling.

Follow-up review on 2026-09-23 preserved the existing uncommitted fixes and checked all 12 shared resource groups and 44 public resource methods. The shared method inventory now detects additions or omissions in either SDK.

## Fixes synchronized

| Behavior | JavaScript | Python |
| --- | --- | --- |
| Card lookup uses `cards/view?card_id=...`, unwraps `card`, rejects missing/mismatched IDs, preserves dimensions | Already fixed | Ported |
| Categories use `categories/list` and unwrap the response envelope | Already fixed | Ported |
| Country code comes from `ups_code`, not numeric `id`; expose numeric ID, aliases, delivery cost | Already fixed | Ported |
| Countries unwrap the `countries` envelope; states come from the selected country’s nested `states`, using `short_name` | Fixed shared bug | Fixed shared bug |
| Saved recipient IDs go in `address_ids`; message/wishes are sent at top level | Already fixed | Already fixed |
| Reject mixed saved IDs and inline recipients in convenience send | Already fixed | Already fixed |
| Reject simultaneous `addresses` and `address_ids` in basket requests | Ported | Already fixed |
| Copy default return-address ID into each inline row without replacing explicit row IDs | Ported | Already fixed |
| Avoid mutating caller-owned inline rows when adding return-address IDs | Covered | Fixed |
| Accept booleans as well as 0/1/2 delivery confirmation | Restored TypeScript compatibility | Already supported |
| Stamp response keys: bare list, `stamp_options`, `stampOptions`, `options`, `results`; label/name/title fallback | Added `options` and `label` | Added `stamp_options` |
| QR creation short response preserves `raw` | Already supported | Ported |
| Invalid scalar recipients fail before any order request | Ported | Already supported |
| Non-JSON HTTP error bodies remain available | Fixed consumed-response-body bug | Already supported |
| Multipart uploads include the selected image type without mutating input | Fixed | Already supported |
| Multipart retries preserve file contents | Fetch reuses FormData | Fixed consumed-stream bug |
| Numeric-string user credits and gift-card amounts become numbers; zero amounts survive | Already supported | Fixed |
| Both delivery-confirmation constant naming conventions work | Added Python aliases | Added JavaScript aliases |

Other historical fixes were present in both: OAuth Bearer and API-key authentication; inline return-address fields; gift-card denominations and response envelope; inserts and historical flag; saved signatures; custom-card lookup; past baskets; batch address deletion; basket inspect/remove/clear; stamp selection.

## Deliberate compatibility differences

- Python categories continue to return dictionaries with API field names. JavaScript returns typed objects with camelCase aliases and `raw`. Python callers retain existing `category["name"]` access; this review does not change that public interface just to match TypeScript types.
- Python uses snake_case methods/arguments, dataclasses and a synchronous requests transport; JavaScript uses camelCase, interfaces and asynchronous fetch. Python-only CLI support and language-specific dependencies are not ported.
- Python Country keeps the existing positional constructor arguments (`code`, `name`, `raw`); new fields have defaults. Numeric country IDs are no longer mistaken for country codes.
- Release versions were not bumped, and no packages were published.

## Verification

Both repositories contain identical `tests/fixtures/sdk-parity.json` data with independent tests of the SDK HTTP boundary. Tests exercise authentication, response envelopes, card dimensions/zero margins, country fields, stamp variants, order payloads, recipient validation, and return-address handling. Order and QR write operations are mocked; no orders were sent.

The 2026-09-23 follow-up passed all 177 JavaScript tests, TypeScript checking, ESM/CJS builds and declaration generation, and all 271 Python tests. Shared fixture copies were checked for equality. Upload tests verify image type, filenames, contents, caller-input preservation in JavaScript, and identical file contents across Python retries. No live API calls or production writes were made during this follow-up; earlier live-check results are not re-certified here.

Keep these fixture copies synchronized when changing either SDK. Run `npm test`, `npm run lint`, `npm run build` in JavaScript and `python -m pytest -q` in Python before release. Passing these checks establishes parity for the reviewed fixes; it is not a live test of every backend operation.
