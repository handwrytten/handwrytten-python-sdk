# Handwrytten Python SDK

The official Python SDK for the [Handwrytten API](https://www.handwrytten.com/api/) — send real handwritten notes at scale using robots with real pens.

## Installation

```bash
pip install handwrytten
```

## Quick Start

```python
from handwrytten import Handwrytten

client = Handwrytten("your_api_key")

# Browse available cards and fonts
cards = client.cards.list()
fonts = client.fonts.list()

# Send a handwritten note in one call
result = client.orders.send(
    card_id=cards[0].id,
    font=fonts[0].id,
    message="Thanks for being an amazing customer!",
    wishes="Best,\nThe Handwrytten Team",
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
        "street1": "123 Main Street",
        "city": "Phoenix",
        "state": "AZ",
        "zip": "85001",
    },
)
```

## Usage

### Send a Single Note

```python
result = client.orders.send(
    card_id="12345",
    font="hwDavid",
    message="Thank you for your business!",
    wishes="Best,\nThe Team",
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
        "street1": "123 Main St",
        "city": "Phoenix",
        "state": "AZ",
        "zip": "85001",
    },
)
```

### Send Bulk — Multiple Recipients with Per-Recipient Overrides

Each recipient can have its own `message`, `wishes`, and `sender`. Top-level values serve as defaults for any recipient that doesn't specify its own.

```python
result = client.orders.send(
    card_id="12345",
    font="hwDavid",
    sender={"firstName": "David", "lastName": "Wachs",
            "street1": "100 S Mill Ave", "city": "Tempe",
            "state": "AZ", "zip": "85281"},
    recipient=[
        {
            "firstName": "Jane",
            "lastName": "Doe",
            "street1": "123 Main St",
            "city": "Phoenix",
            "state": "AZ",
            "zip": "85001",
            "message": "Thanks for your loyalty, Jane!",
            "wishes": "Warmly,\nThe Team",
        },
        {
            "firstName": "John",
            "lastName": "Smith",
            "street1": "456 Oak Ave",
            "city": "Tempe",
            "state": "AZ",
            "zip": "85281",
            "message": "Great working with you, John!",
            "sender": {"firstName": "Other", "lastName": "Person",
                       "street1": "789 Elm St", "city": "Mesa",
                       "state": "AZ", "zip": "85201"},
        },
    ],
)
```

### Use Saved Address IDs

If you have addresses saved in your Handwrytten account, pass their IDs directly:

```python
result = client.orders.send(
    card_id="12345",
    font="hwDavid",
    message="Thank you!",
    sender=98765,    # saved return-address ID
    recipient=67890, # saved recipient address ID
)

# Mix saved IDs and inline addresses in a bulk send
result = client.orders.send(
    card_id="12345",
    font="hwDavid",
    message="Hello!",
    sender=98765,
    recipient=[
        67890,  # saved address ID
        {"firstName": "Jane", "lastName": "Doe",
         "street1": "123 Main St", "city": "Phoenix",
         "state": "AZ", "zip": "85001"},
    ],
)
```

### Use Typed Models

```python
from handwrytten import Recipient, Sender

sender = Sender(
    first_name="David",
    last_name="Wachs",
    street1="100 S Mill Ave",
    city="Tempe",
    state="AZ",
    zip="85281",
)

recipient = Recipient(
    first_name="Jane",
    last_name="Doe",
    street1="123 Main Street",
    city="Phoenix",
    state="AZ",
    zip="85001",
)

result = client.orders.send(
    card_id="12345",
    font="hwDavid",
    message="Welcome aboard!",
    sender=sender,
    recipient=recipient,
)
```

### Custom Cards

Create custom cards with your own cover images and logos.

```python
# 1. Get available card dimensions
dims = client.custom_cards.dimensions()
for d in dims:
    print(d.id, d)  # e.g. "1 7.000x5.000 flat (landscape)"

# Filter by format and/or orientation
flat_dims = client.custom_cards.dimensions(format="flat")
landscape = client.custom_cards.dimensions(format="flat", orientation="landscape")

# 2. Upload a full-bleed cover image (front of card)
cover = client.custom_cards.upload_image(
    url="https://example.com/cover.jpg",
    image_type="cover",
)

# 3. Upload a logo (appears on the writing side)
logo = client.custom_cards.upload_image(
    url="https://example.com/logo.png",
    image_type="logo",
)

# Or upload from a local file
logo = client.custom_cards.upload_image(
    file_path="/path/to/logo.png",
    image_type="logo",
)

# 4. Check image quality (optional)
check = client.custom_cards.check_image(image_id=logo.id)

# 5. Create the custom card
card = client.custom_cards.create(
    name="My Custom Card",
    dimension_id=dims[0].id,           # card dimension
    cover_id=cover.id,                 # front cover image
    header_logo_id=logo.id,            # logo on writing side
    header_logo_size_percent=80,
)

# 6. Use the new card to send orders
client.orders.send(
    card_id=str(card.card_id),
    font="hwDavid",
    message="Hello from our custom card!",
    recipient={...},
)
```

Custom cards support text and logos in multiple zones:

| Zone | Logo field | Text field | Font field |
|---|---|---|---|
| Header (top of writing side) | `header_logo_id` | `header_text` | `header_font_id` |
| Main (center, folded cards) | `main_logo_id` | `main_text` | `main_font_id` |
| Footer (bottom of writing side) | `footer_logo_id` | `footer_text` | `footer_font_id` |
| Back | `back_logo_id` | `back_text` | `back_font_id` |
| Front cover | `cover_id` | — | — |
| Back cover | `back_cover_id` | — | — |

Font IDs for text zones come from `client.fonts.list_for_customizer()` (printed/typeset fonts), which are different from the handwriting fonts used in `client.fonts.list()`.

### Manage Custom Images

```python
# List all uploaded images
images = client.custom_cards.list_images()
for img in images:
    print(img.id, img.image_type, img.image_url)

# Filter by type
covers = client.custom_cards.list_images(image_type="cover")
logos = client.custom_cards.list_images(image_type="logo")

# Get details of a custom card
card = client.custom_cards.get(card_id=456)

# Delete an image
client.custom_cards.delete_image(image_id=123)

# Delete a custom card
client.custom_cards.delete(card_id=456)
```

### Browse Cards and Fonts

```python
# Card templates
cards = client.cards.list()
card = client.cards.get("12345")
categories = client.cards.categories()

# Handwriting fonts (for orders)
fonts = client.fonts.list()
for font in fonts:
    print(f"{font.id}: {font.label}")

# Customizer fonts (for custom card text zones)
customizer_fonts = client.fonts.list_for_customizer()
```

### Gift Cards and Inserts

```python
# List gift cards with their denominations (price points)
gift_cards = client.gift_cards.list()
for gc in gift_cards:
    print(f"{gc.title}: {len(gc.denominations)} denominations")
    for d in gc.denominations:
        print(f"  ${d.nominal} (price: ${d.price})")

# Include a gift card denomination in an order
client.orders.send(
    card_id="12345",
    font="hwDavid",
    message="Enjoy!",
    denomination_id=gc.denominations[0].id,
    recipient={...},
)

# List inserts (optionally include historical/discontinued)
inserts = client.inserts.list()
all_inserts = client.inserts.list(include_historical=True)

# Include an insert in an order
client.orders.send(
    card_id="12345",
    font="hwDavid",
    message="Hello!",
    insert_id=inserts[0].id,
    recipient={...},
)
```

### QR Codes

Create QR codes and attach them to custom cards.

```python
from handwrytten import QRCodeLocation

# Create a QR code
qr = client.qr_codes.create(name="Website Link", url="https://example.com")

# List existing QR codes
qr_codes = client.qr_codes.list()

# Browse available frames (decorative borders around the QR code)
frames = client.qr_codes.frames()

# Attach a QR code to a custom card
card = client.custom_cards.create(
    name="Card with QR",
    dimension_id=dims[0].id,
    cover_id=cover.id,
    qr_code_id=int(qr.id),
    qr_code_location=QRCodeLocation.FOOTER,  # HEADER, FOOTER, or MAIN
    qr_code_size_percent=30,
    qr_code_align="right",
)

# Delete a QR code
client.qr_codes.delete(qr_code_id=int(qr.id))
```

### Address Book

Save and manage recipient and sender addresses, then use their IDs when sending orders.

```python
# Save a sender (return address)
sender_id = client.address_book.add_sender(
    first_name="David",
    last_name="Wachs",
    street1="100 S Mill Ave",
    city="Tempe",
    state="AZ",
    zip="85281",
)

# Save a recipient
recipient_id = client.address_book.add_recipient(
    first_name="Jane",
    last_name="Doe",
    street1="123 Main St",
    city="Phoenix",
    state="AZ",
    zip="85001",
)

# Send using saved IDs
client.orders.send(
    card_id="12345",
    font="hwDavid",
    message="Hello!",
    sender=sender_id,
    recipient=recipient_id,
)

# Update a recipient
client.address_book.update_recipient(
    address_id=recipient_id,
    street1="456 New St",
    city="Scottsdale",
)

# List saved addresses
senders = client.address_book.list_senders()
recipients = client.address_book.list_recipients()
for r in recipients:
    print(r.id, r)  # e.g. "123 Jane Doe, 456 New St, Scottsdale, AZ 85001"

# Delete addresses
client.address_book.delete_recipient(address_id=recipient_id)
client.address_book.delete_sender(address_id=sender_id)

# Batch delete
client.address_book.delete_recipient(address_ids=[1, 2, 3])

# Countries and states
countries = client.address_book.countries()
states = client.address_book.states("US")
```

### Signatures

List the user's saved handwriting signatures for use in orders.

```python
signatures = client.auth.list_signatures()
for sig in signatures:
    print(f"  [{sig.id}] preview={sig.preview}")
```

### Two-Step Basket Workflow

For finer control, use `client.basket` directly instead of `client.orders.send()`:

```python
# Step 1: Add order(s) to the basket
client.basket.add_order(
    card_id="12345",
    font="hwDavid",
    addresses=[{
        "firstName": "Jane",
        "lastName": "Doe",
        "street1": "123 Main St",
        "city": "Phoenix",
        "state": "AZ",
        "zip": "85001",
        "message": "Hello!",
    }],
)

# Step 2: Submit the basket
result = client.basket.send()

# Inspect the basket before sending
basket = client.basket.list()          # all items with totals
item = client.basket.get_item(9517)    # single item by basket_id
n = client.basket.count()              # number of items

# Remove a specific item or clear everything
client.basket.remove(basket_id=9517)
client.basket.clear()

# List previously submitted baskets
past = client.orders.list_past_baskets(page=1)
```

### Error Handling

```python
from handwrytten import (
    HandwryttenError,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
)

try:
    result = client.orders.send(...)
except AuthenticationError:
    print("Check your API key")
except BadRequestError as e:
    print(f"Invalid request: {e.message}")
    print(f"Details: {e.response_body}")
except RateLimitError as e:
    print(f"Rate limited — retry after {e.retry_after}s")
except HandwryttenError as e:
    print(f"API error: {e}")
```

## API Resources

| Resource | Methods |
|---|---|
| `client.auth` | `get_user()`, `login()`, `list_signatures()` |
| `client.cards` | `list()`, `get(id)`, `categories()` |
| `client.custom_cards` | `dimensions()`, `upload_image()`, `check_image()`, `list_images()`, `delete_image()`, `create()`, `get()`, `delete()` |
| `client.fonts` | `list()`, `list_for_customizer()` |
| `client.gift_cards` | `list()` |
| `client.inserts` | `list(include_historical)` |
| `client.qr_codes` | `list()`, `create()`, `delete()`, `frames()` |
| `client.address_book` | `list_recipients()`, `add_recipient()`, `update_recipient()`, `delete_recipient()`, `list_senders()`, `add_sender()`, `delete_sender()`, `countries()`, `states(country)` |
| `client.orders` | `send()`, `get(id)`, `list()`, `list_past_baskets()` |
| `client.basket` | `add_order()`, `send()`, `remove(basket_id)`, `clear()`, `list()`, `get_item(basket_id)`, `count()` |
| `client.prospecting` | `calculate_targets(zip, radius)` |

## Configuration

```python
client = Handwrytten(
    api_key="your_key",
    timeout=60,          # seconds
    max_retries=5,       # automatic retries with exponential backoff
)
```

## Full Example

See [`examples/example.py`](examples/example.py) for a complete working demo that exercises every resource: listing cards/fonts, sending single and bulk orders, uploading custom images, creating custom cards, and cleanup.

## Requirements

- Python 3.8+
- `requests`

## License

MIT
