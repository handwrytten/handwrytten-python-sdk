"""Quick test script for the Handwrytten SDK."""

import os
import random # qr codes must have unique names, so we use this to generate a random number for the name in this example

from handwrytten import Handwrytten, HandwryttenError, QRCodeLocation, ZoneType

# Set your API key here or via the HANDWRYTTEN_API_KEY environment variable
API_KEY = os.environ.get("HANDWRYTTEN_API_KEY", "<your_api_key_here>")


def main():
    client = Handwrytten(API_KEY)
    print(f"Client initialized: {client}\n")

    # 1. Get current user
    print("--- User Info ---")
    user = client.auth.get_user()
    print(f"  Email: {user.email}")
    print()

    # 2. List available cards
    print("--- Cards (first 5) ---")
    cards = client.cards.list()
    for card in cards[:5]:
        print(f"  [{card.id}] {card.title}")
    print(f"  ... {len(cards)} total cards")
    print()

    # 3. List available handwriting fonts
    print("--- Handwriting Fonts (first 5) ---")
    fonts = client.fonts.list()
    for font in fonts[:5]:
        print(f"  [{font.id}] {font.label}")
    print(f"  ... {len(fonts)} total fonts")
    print()

    # 4. List customizer fonts (for custom card text zones)
    print("--- Customizer Fonts (first 5) ---")
    customizer_fonts = client.fonts.list_for_customizer()
    for f in customizer_fonts[:5]:
        print(f"  [{f.get('id')}] {f.get('label')}")
    print(f"  ... {len(customizer_fonts)} total customizer fonts")
    print()

    # 5. List gift cards with denominations
    print("--- Gift Cards ---")
    gift_cards = client.gift_cards.list()
    for gc in gift_cards[:5]:
        print(f"  [{gc.id}] {gc.title} ({len(gc.denominations)} denominations)")
        for d in gc.denominations[:3]:
            print(f"       ${d.nominal} (price: ${d.price})")
    print(f"  ... {len(gift_cards)} total gift cards")
    print()

    # 5b. List inserts (including historical)
    print("--- Inserts ---")
    inserts = client.inserts.list()
    print(f"  Active inserts: {len(inserts)}")
    all_inserts = client.inserts.list(include_historical=True)
    print(f"  All inserts (incl. historical): {len(all_inserts)}")
    print()

    # 5c. List signatures
    print("--- Signatures ---")
    signatures = client.auth.list_signatures()
    for sig in signatures[:5]:
        print(f"  [{sig.id}] preview={sig.preview or 'N/A'}")
    print(f"  ... {len(signatures)} total signatures")
    print()

    # 6. List orders
    print("--- Recent Orders ---")
    orders = client.orders.list(page=1, per_page=5)
    if orders:
        for order in orders[:5]:
            print(f"  [{order.id}] status={order.status}")
    else:
        print("  No orders found.")
    print()

    # 7. Send a single order with sender
    print("--- Send Single Order ---")
    print(f"  Using card_id={cards[0].id}, font={fonts[0].id}")
    client.orders.send(
        card_id=cards[0].id,
        font=fonts[0].id,
        message="Thanks for being an amazing customer!",
        wishes="Best,\nThe Handwrytten Team",
        sender={
            "firstName": "David",
            "lastName": "Wachs",
            "street1": "3433 E Main Ave",
            "city": "Phoenix",
            "state": "AZ",
            "zip": "85018",
        },
        recipient={
            "firstName": "Jane",
            "lastName": "Doe",
            "street1": "3433 E Main Ave",
            "city": "Phoenix",
            "state": "AZ",
            "zip": "85001",
        },
    )
    print("  Order sent!")
    print()

    # 7b. Send an order with a gift card denomination and an insert
    if gift_cards and gift_cards[0].denominations and inserts:
        print("--- Send Order with Gift Card & Insert ---")
        client.orders.send(
            card_id=cards[0].id,
            font=fonts[0].id,
            message="Enjoy this gift!",
            denomination_id=gift_cards[0].denominations[0].id,
            insert_id=inserts[0].id,
            sender={
                "firstName": "David",
                "lastName": "Wachs",
                "street1": "3433 E Main Ave",
                "city": "Phoenix",
                "state": "AZ",
                "zip": "85018",
            },
            recipient={
                "firstName": "Jane",
                "lastName": "Doe",
                "street1": "3433 E Main Ave",
                "city": "Phoenix",
                "state": "AZ",
                "zip": "85001",
            },
        )
        print("  Order with gift card & insert sent!")
        print()

    # 8. Send bulk — multiple recipients with per-recipient messages
    print("--- Send Bulk Order ---")
    client.orders.send(
        card_id=cards[0].id,
        font=fonts[0].id,
        sender={
            "firstName": "David",
            "lastName": "Wachs",
            "street1": "3433 E Main Ave",
            "city": "Phoenix",
            "state": "AZ",
            "zip": "85018",
        },
        recipient=[
            {
                "firstName": "Jane",
                "lastName": "Doe",
                "street1": "3433 E Main Ave",
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
                "wishes": "Cheers,\nThe Team",
            },
        ],
    )
    print("  Bulk order sent!")
    print()

    # 9. Address Book — save and list addresses
    print("--- Address Book ---")

    # Save a sender (return address)
    sender_id = client.address_book.add_sender(
        first_name="David",
        last_name="Wachs",
        street1="3433 E Main Ave",
        city="Phoenix",
        state="AZ",
        zip="85018",
    )
    print(f"  Saved sender address: id={sender_id}")

    # Save a recipient
    recipient_id = client.address_book.add_recipient(
        first_name="Jane",
        last_name="Doe",
        street1="3433 E Main Ave",
        city="Phoenix",
        state="AZ",
        zip="85001",
    )
    print(f"  Saved recipient address: id={recipient_id}")

    # List saved senders
    senders = client.address_book.list_senders()
    print(f"  Saved senders: {len(senders)}")
    for s in senders[:3]:
        print(f"    [{s.id}] {s}")

    # List saved recipients
    recipients = client.address_book.list_recipients()
    print(f"  Saved recipients: {len(recipients)}")
    for r in recipients[:3]:
        print(f"    [{r.id}] {r}")

    # Send an order using saved address IDs
    print("  Sending order with saved address IDs...")
    client.orders.send(
        card_id=cards[0].id,
        font=fonts[0].id,
        message="Hello from saved addresses!",
        sender=sender_id,
        recipient=recipient_id,
    )
    print("  Order with saved addresses sent!")
    print()

    # 10. Two-step basket workflow
    print("--- Two-Step Basket Order ---")

    # Inspect the basket before adding anything
    print(f"  Items in basket: {client.basket.count()}")

    # Step 1: Add order(s) to the basket
    place_result = client.basket.add_order(
        card_id=cards[0].id,
        font=fonts[0].id,
        return_address_id=sender_id,
        addresses=[{
            "firstName": "Jane",
            "lastName": "Doe",
            "street1": "3433 E Main Ave",
            "city": "Phoenix",
            "state": "AZ",
            "zip": "85001",
            "message": "Hello from the basket workflow!",
            "wishes": "Best,\nThe Team",
        }],
    )
    print(f"  Order added to basket. order_id={place_result.get('order_id')}")

    # List all items currently in the basket
    basket = client.basket.list()
    print(f"  Basket now has {client.basket.count()} item(s), grand total: {basket.get('totals', {}).get('grand_total')}")
    for item in basket.get("items", []):
        basket_id = item.get("basket_id")
        print(f"    basket_id={basket_id} status={item.get('status')} price={item.get('price')}")

    # Fetch a single basket item by basket_id
    if basket.get("items"):
        basket_id = basket["items"][0]["basket_id"]
        item_detail = client.basket.get_item(basket_id)
        print(f"  Item detail: basket_id={basket_id} font={item_detail.get('item', {}).get('font')}")

        # Remove that item from the basket
        client.basket.remove(basket_id=basket_id)
        print(f"  Removed basket_id={basket_id}. Items remaining: {client.basket.count()}")

    # Add a fresh order and submit it
    client.basket.add_order(
        card_id=cards[0].id,
        font=fonts[0].id,
        return_address_id=sender_id,
        addresses=[{
            "firstName": "Jane",
            "lastName": "Doe",
            "street1": "3433 E Main Ave",
            "city": "Phoenix",
            "state": "AZ",
            "zip": "85001",
            "message": "Hello from the basket workflow!",
            "wishes": "Best,\nThe Team",
        }],
    )
    # Step 2: Submit the basket
    result = client.basket.send()
    print(f"  Basket sent! {result}")

    # Clear any leftover items
    client.basket.clear()
    print(f"  Basket cleared. Items remaining: {client.basket.count()}")
    print()

    # 11. Custom cards — upload images and create a card
    print("--- Custom Cards ---")

    # Get available card dimensions (filter for flat landscape)
    all_dims = client.custom_cards.dimensions()
    print(f"  All dimensions: {len(all_dims)}")
    for d in all_dims:
        print(f"    [{d.id}] {d}")

    flat_dims = client.custom_cards.dimensions(format="flat")
    print(f"  Flat dimensions: {len(flat_dims)}")

    # List existing uploaded images
    images = client.custom_cards.list_images()
    print(f"  Existing custom images: {len(images)}")
    for img in images[:3]:
        print(f"    [{img.id}] type={img.image_type} url={img.image_url or ''}")

    # Upload a cover image by URL
    print("  Uploading cover image...")
    cover = client.custom_cards.upload_image(
        url="https://cdn.handwrytten.com/www/2026/01/5-Strategic-Ways-hero-scaled.jpg",
        image_type="cover",
    )
    print(f"    Cover uploaded: id={cover.id}, url={cover.image_url}")

    # Upload a logo image by URL
    print("  Uploading logo image...")
    logo = client.custom_cards.upload_image(
        url="https://webcdn.handwrytten.com/wp-content/themes/handwrytten/images/logo@2x.png",
        image_type="logo",
    )
    print(f"    Logo uploaded: id={logo.id}, url={logo.image_url}")

    # Create a QR code
    print("  Creating QR code...")
    qr = client.qr_codes.create(
         # qr codes must have unique names, so we generate a random number for the name in this example
        name=f"SDK Test QR {random.randint(100000, 999999)} ",
        url="https://www.handwrytten.com",
    )
    print(f"    QR code created: id={qr.id}")

    # List QR code frames
    frames = client.qr_codes.frames()
    print(f"  Available QR code frames: {len(frames)}")
    for f in frames:
        print(f"    [{f.get('id')}] type={f.get('type')} url={f.get('url')}")

    # Create a custom card with a QR code
    print("  Creating custom card with QR code...")
    custom_card = client.custom_cards.create(
        name="SDK Test Card",
        dimension_id=all_dims[0].id,
        cover_id=cover.id,
        header_type=ZoneType.LOGO,
        header_logo_id=logo.id,
        header_logo_size_percent=80,
        qr_code_id=int(qr.id),
        qr_code_location=QRCodeLocation.FOOTER,
        qr_code_size_percent=100,
    )
    print(f"    Custom card created: card_id={custom_card.card_id}")

    # Get details of the custom card we just created
    card_detail = client.custom_cards.get(card_id=custom_card.card_id)
    print(f"    Custom card detail: card_id={card_detail.card_id}")
    print()

    # 12. Send an order using the custom card
    print("--- Send Order with Custom Card ---")
    client.orders.send(
        card_id=str(custom_card.card_id),
        font=fonts[0].id,
        message="Hello from our custom card!",
        recipient={
            "firstName": "Jane",
            "lastName": "Doe",
            "street1": "3433 E Main Ave",
            "city": "Phoenix",
            "state": "AZ",
            "zip": "85001",
        },
    )
    print("  Custom card order sent!")
    print()

    # 13. List past baskets
    print("--- Past Baskets ---")
    past_baskets = client.orders.list_past_baskets(page=1)
    print(f"  Past baskets: {len(past_baskets)}")
    for pb in past_baskets[:3]:
        print(f"    {pb}")
    print()

    # 14. Delete saved addresses
    print("--- Delete Saved Addresses ---")
    client.address_book.delete_recipient(address_id=recipient_id)
    print(f"  Deleted recipient address: id={recipient_id}")
    client.address_book.delete_sender(address_id=sender_id)
    print(f"  Deleted sender address: id={sender_id}")
    print()

    # Clean up: delete the custom card and images
    # print("--- Cleanup ---")
    # client.custom_cards.delete(card_id=custom_card.card_id)
    # print(f"  Deleted custom card {custom_card.card_id}")
    # client.custom_cards.delete_image(image_id=cover.id)
    # print(f"  Deleted cover image {cover.id}")
    # client.custom_cards.delete_image(image_id=logo.id)
    # print(f"  Deleted logo image {logo.id}")
    # client.qr_codes.delete(qr_code_id=int(qr.id))
    # print(f"  Deleted QR code {qr.id}")

    print("\nAll done!")


if __name__ == "__main__":
    try:
        main()
    except HandwryttenError as e:
        print(f"\nAPI error: {e}")
        if hasattr(e, "response_body"):
            print(f"Full response body: {e.response_body}")
