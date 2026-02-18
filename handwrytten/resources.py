"""API resource classes — each maps to a section of the Handwrytten API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from handwrytten.http_client import HttpClient
from handwrytten.models import (
    Card,
    Country,
    CustomCard,
    CustomImage,
    Dimension,
    Font,
    GiftCard,
    Insert,
    Order,
    QRCode,
    Recipient,
    SavedAddress,
    Sender,
    State,
    User,
)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class AuthResource:
    """Authentication and user profile endpoints."""

    def __init__(self, http: HttpClient):
        self._http = http

    def get_user(self) -> User:
        """Get the authenticated user's profile.

        Returns:
            User object with account details.
        """
        data = self._http.get("auth/getUser")
        return User.from_dict(data if isinstance(data, dict) else {})

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate with email/password and retrieve a UID.

        Most integrations should use an API key instead.

        Args:
            email: Account email.
            password: Account password.

        Returns:
            Dict containing uid and session info.
        """
        return self._http.post(
            "auth/authorization",
            json_body={"login": email, "password": password},
        )


# ---------------------------------------------------------------------------
# Cards
# ---------------------------------------------------------------------------

class CardsResource:
    """Browse card and stationery templates."""

    def __init__(self, http: HttpClient):
        self._http = http

    def list(self) -> List[Card]:
        """Get all available card templates.

        Returns:
            List of Card objects.

        Example:
            >>> cards = client.cards.list()
            >>> for card in cards:
            ...     print(card.id, card.title)
        """
        data = self._http.get("cards/list")
        items = data if isinstance(data, list) else data.get("results", data.get("cards", []))
        return [Card.from_dict(c) for c in items]

    def get(self, card_id: str) -> Card:
        """Get a single card by ID.

        Args:
            card_id: The card's unique identifier.

        Returns:
            Card object.
        """
        data = self._http.get(f"cards/get/{card_id}")
        return Card.from_dict(data if isinstance(data, dict) else {})

    def categories(self) -> List[Dict[str, Any]]:
        """Get available card categories.

        Returns:
            List of category dicts.
        """
        data = self._http.get("cards/categories")
        return data if isinstance(data, list) else []


# ---------------------------------------------------------------------------
# Custom Cards
# ---------------------------------------------------------------------------

class CustomCardsResource:
    """Upload images and create custom card designs.

    Typical workflow:
        1. Upload a cover and/or logo image with ``upload_image()``.
        2. (Optional) Verify image quality with ``check_image()``.
        3. Create the custom card with ``create()``, referencing the
           uploaded image IDs.

    Example::

        # Get available card dimensions
        dims = client.custom_cards.dimensions(format="flat")

        # Upload a full-bleed cover for the front of the card
        cover = client.custom_cards.upload_image(
            url="https://example.com/cover.jpg", image_type="cover",
        )

        # Upload a logo for the writing side
        logo = client.custom_cards.upload_image(
            url="https://example.com/logo.png", image_type="logo",
        )

        # Create the card
        card = client.custom_cards.create(
            name="My Custom Card",
            dimension_id=dims[0].id,
            cover_id=cover.id,
            header_logo_id=logo.id,
        )
    """

    def __init__(self, http: HttpClient):
        self._http = http

    # -- Dimensions ---------------------------------------------------------

    def dimensions(
        self,
        format: Optional[str] = None,
        orientation: Optional[str] = None,
    ) -> List[Dimension]:
        """Get customizable card dimensions.

        Use these dimension IDs when creating custom cards with ``create()``.

        Args:
            format: Filter by ``"flat"`` or ``"folded"``.
            orientation: Filter by ``"landscape"`` or ``"portrait"``.

        Returns:
            List of Dimension objects.

        Example:
            >>> dims = client.custom_cards.dimensions(format="flat")
            >>> for d in dims:
            ...     print(d.id, d)
        """
        data = self._http.get("design/dimensions")
        if isinstance(data, dict):
            items = data.get("dimensions", data.get("results", []))
        elif isinstance(data, list):
            items = data
        else:
            items = []

        dims = [Dimension.from_dict(d) for d in items]
        if format is not None:
            dims = [d for d in dims if d.format == format]
        if orientation is not None:
            dims = [d for d in dims if d.orientation == orientation]
        return dims

    # -- Image management ---------------------------------------------------

    def upload_image(
        self,
        *,
        url: Optional[str] = None,
        file_path: Optional[str] = None,
        image_type: str = "logo",
    ) -> CustomImage:
        """Upload a custom image for use with custom cards.

        Provide **one** of ``url`` or ``file_path``.

        Args:
            url: Publicly accessible URL of the image (JPEG/PNG/GIF).
            file_path: Local file path to upload.
            image_type: ``"logo"`` (writing-side logo) or ``"cover"``
                (full-bleed front/back image).

        Returns:
            CustomImage with ``id`` and ``image_url``.
        """
        if url and file_path:
            raise ValueError("Provide either url or file_path, not both")
        if not url and not file_path:
            raise ValueError("Provide either url or file_path")

        if url:
            body: Dict[str, Any] = {"url": url, "type": image_type}
            data = self._http.post("cards/uploadCustomLogo", json_body=body)
        else:
            # File upload via multipart/form-data
            import mimetypes
            mime = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
            with open(file_path, "rb") as f:
                data = self._http.post_multipart(
                    "cards/uploadCustomLogo",
                    files={"file": (file_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1], f, mime)},
                    data={"type": image_type},
                )
        return CustomImage.from_dict(data if isinstance(data, dict) else {})

    def check_image(
        self, image_id: int, card_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Check if an uploaded image meets quality requirements.

        Args:
            image_id: ID returned by ``upload_image()``.
            card_id: Optional base card ID to validate dimensions against.

        Returns:
            Dict with ``status``, optional ``warning``, and optional ``error``.
        """
        body: Dict[str, Any] = {"image_id": image_id}
        if card_id is not None:
            body["card_id"] = card_id
        return self._http.post("cards/checkUploadedCustomLogo", json_body=body)

    def list_images(
        self, image_type: Optional[str] = None
    ) -> List[CustomImage]:
        """List previously uploaded custom images.

        Args:
            image_type: Filter by ``"logo"`` or ``"cover"``. ``None`` returns
                all images.

        Returns:
            List of CustomImage objects.
        """
        params: Dict[str, Any] = {}
        if image_type is not None:
            params["type"] = image_type
        data = self._http.get("cards/listCustomUserImages", params=params)
        if isinstance(data, dict):
            items = data.get("images", [])
        elif isinstance(data, list):
            items = data
        else:
            items = []
        return [CustomImage.from_dict(img) for img in items]

    def delete_image(self, image_id: int) -> Dict[str, Any]:
        """Delete an uploaded custom image.

        Args:
            image_id: ID of the image to delete.
        """
        return self._http.post(
            "cards/deleteCustomLogo", json_body={"image_id": image_id}
        )

    # -- Card creation / deletion -------------------------------------------

    def create(
        self,
        name: str,
        dimension_id: str,
        *,
        is_update: Optional[bool] = None,
        # Cover (front)
        cover_id: Optional[int] = None,
        preset_cover_id: Optional[int] = None,
        cover_size_percent: Optional[int] = None,
        # Header (writing side — top area)
        header_type: Optional[str] = None,
        header_text: Optional[str] = None,
        header_font_id: Optional[str] = None,
        header_font_size: Optional[int] = None,
        header_font_color: Optional[str] = None,
        header_align: Optional[str] = None,
        header_logo_id: Optional[int] = None,
        header_logo_size_percent: Optional[int] = None,
        # Main (writing side — center, folded cards only)
        main_type: Optional[str] = None,
        main_text: Optional[str] = None,
        main_font_id: Optional[str] = None,
        main_font_size: Optional[int] = None,
        main_font_color: Optional[str] = None,
        main_align: Optional[str] = None,
        main_logo_id: Optional[int] = None,
        main_logo_size_percent: Optional[int] = None,
        # Footer (writing side — bottom area)
        footer_type: Optional[str] = None,
        footer_text: Optional[str] = None,
        footer_font_id: Optional[str] = None,
        footer_font_size: Optional[int] = None,
        footer_font_color: Optional[str] = None,
        footer_align: Optional[str] = None,
        footer_logo_id: Optional[int] = None,
        footer_logo_size_percent: Optional[int] = None,
        # Back
        back_cover_id: Optional[int] = None,
        preset_back_cover_id: Optional[int] = None,
        back_type: Optional[str] = None,
        back_align: Optional[str] = None,
        back_vertical_align: Optional[str] = None,
        back_logo_id: Optional[int] = None,
        back_text: Optional[str] = None,
        back_font_id: Optional[int] = None,
        back_font_size: Optional[int] = None,
        back_font_color: Optional[str] = None,
        back_size_percent: Optional[int] = None,
        # QR Code
        qr_code_id: Optional[int] = None,
        qr_code_size_percent: Optional[int] = None,
        qr_code_align: Optional[str] = None,
        qr_code_location: Optional[str] = None,
        qr_code_frame_id: Optional[int] = None,
        **extra: Any,
    ) -> CustomCard:
        """Create a custom card from uploaded images and text.

        Args:
            name: Display name for the custom card.
            dimension_id: Card dimension ID (from ``dimensions()``).
            is_update: ``True`` to create a new version of an existing card
                while preserving order history.
            cover_id: Uploaded "cover" image ID for the front.
            preset_cover_id: Preset "front"/"mixed" image ID for the front.
            cover_size_percent: Cover image size percentage.
            header_type: ``"text"`` or ``"logo"`` for the header area.
            header_text: Text for the header (used when header_type is
                ``"text"`` or no logo is specified).
            header_font_id: Font ID for header text.
            header_font_size: Font size for header text.
            header_font_color: Hex colour for header text (e.g. ``"#000000"``).
            header_align: ``"left"``, ``"center"``, or ``"right"``.
            header_logo_id: Uploaded "logo" image ID for the header.
            header_logo_size_percent: Header logo size percentage.
            main_type: ``"text"`` or ``"logo"`` for the main area (folded
                cards only).
            main_text: Text for the main area.
            main_font_id: Font ID for main text.
            main_font_size: Font size for main text.
            main_font_color: Hex colour for main text.
            main_align: ``"left"``, ``"center"``, or ``"right"``.
            main_logo_id: Uploaded "logo" image ID for the main area.
            main_logo_size_percent: Main logo size percentage.
            footer_type: ``"text"`` or ``"logo"`` for the footer area.
            footer_text: Text for the footer.
            footer_font_id: Font ID for footer text.
            footer_font_size: Font size for footer text.
            footer_font_color: Hex colour for footer text.
            footer_align: ``"left"``, ``"center"``, or ``"right"``.
            footer_logo_id: Uploaded "logo" image ID for the footer.
            footer_logo_size_percent: Footer logo size percentage.
            back_cover_id: Uploaded "cover" image ID for the back.
            preset_back_cover_id: Preset "back"/"mixed" image ID for
                the back.
            back_type: ``"cover"`` or ``"logo"`` for the back.
            back_align: ``"left"``, ``"center"``, or ``"right"``.
            back_vertical_align: ``"center"`` or ``"bottom"``.
            back_logo_id: Uploaded "logo" image ID for the back.
            back_text: Text for the back.
            back_font_id: Font ID for back text.
            back_font_size: Font size for back text.
            back_font_color: Hex colour for back text.
            back_size_percent: Back image size percentage.
            qr_code_id: QR code ID to attach.
            qr_code_size_percent: QR code size percentage.
            qr_code_align: ``"left"``, ``"center"``, or ``"right"``.
            qr_code_location: ``"main"``, ``"header"``, or ``"footer"``.
            qr_code_frame_id: QR code frame ID.
            **extra: Additional API parameters.

        Returns:
            CustomCard with ``card_id`` of the newly created card.
        """
        body: Dict[str, Any] = {"name": name, "dimension_id": dimension_id}

        if is_update is not None:
            body["is_update"] = is_update

        # Collect all optional fields — skip None values
        _optional = {
            "cover_id": cover_id,
            "preset_cover_id": preset_cover_id,
            "cover_size_percent": cover_size_percent,
            "header_type": header_type,
            "header_text": header_text,
            "header_font_id": header_font_id,
            "header_font_size": header_font_size,
            "header_font_color": header_font_color,
            "header_align": header_align,
            "header_logo_id": header_logo_id,
            "header_logo_size_percent": header_logo_size_percent,
            "main_type": main_type,
            "main_text": main_text,
            "main_font_id": main_font_id,
            "main_font_size": main_font_size,
            "main_font_color": main_font_color,
            "main_align": main_align,
            "main_logo_id": main_logo_id,
            "main_logo_size_percent": main_logo_size_percent,
            "footer_type": footer_type,
            "footer_text": footer_text,
            "footer_font_id": footer_font_id,
            "footer_font_size": footer_font_size,
            "footer_font_color": footer_font_color,
            "footer_align": footer_align,
            "footer_logo_id": footer_logo_id,
            "footer_logo_size_percent": footer_logo_size_percent,
            "back_cover_id": back_cover_id,
            "preset_back_cover_id": preset_back_cover_id,
            "back_type": back_type,
            "back_align": back_align,
            "back_vertical_align": back_vertical_align,
            "back_logo_id": back_logo_id,
            "back_text": back_text,
            "back_font_id": back_font_id,
            "back_font_size": back_font_size,
            "back_font_color": back_font_color,
            "back_size_percent": back_size_percent,
            "qr_code_id": qr_code_id,
            "qr_code_size_percent": qr_code_size_percent,
            "qr_code_align": qr_code_align,
            "qr_code_location": qr_code_location,
            "qr_code_frame_id": qr_code_frame_id,
        }
        body.update({k: v for k, v in _optional.items() if v is not None})
        body.update(extra)

        data = self._http.post("cards/createCustomCard", json_body=body)
        return CustomCard.from_dict(data if isinstance(data, dict) else {})

    def delete(self, card_id: int) -> Dict[str, Any]:
        """Delete a custom card.

        Args:
            card_id: ID of the custom card to delete.
        """
        return self._http.post(
            "design/delete", json_body={"id": card_id}
        )


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

class FontsResource:
    """Browse handwriting styles (fonts)."""

    def __init__(self, http: HttpClient):
        self._http = http

    def list(self) -> List[Font]:
        """Get all available handwriting fonts.

        Returns:
            List of Font objects.

        Example:
            >>> fonts = client.fonts.list()
            >>> for font in fonts:
            ...     print(font.id, font.name)
        """
        data = self._http.get("fonts/list")
        items = data if isinstance(data, list) else data.get("results", data.get("fonts", []))
        return [Font.from_dict(f) for f in items]

    def list_for_customizer(self) -> List[Dict[str, Any]]:
        """Get fonts available for the card customizer.

        These are printed/typeset fonts used in custom card design
        (header, footer, main, back text) — different from handwriting
        fonts returned by ``list()``.

        Returns:
            List of font dicts with ``id``, ``name``, ``label``,
            ``font_file``.

        Example:
            >>> customizer_fonts = client.fonts.list_for_customizer()
            >>> for f in customizer_fonts:
            ...     print(f["id"], f["label"])
        """
        data = self._http.get("fonts/listForCustomizer")
        if isinstance(data, dict):
            return data.get("fonts", [])
        return data if isinstance(data, list) else []


# ---------------------------------------------------------------------------
# Gift Cards
# ---------------------------------------------------------------------------

class GiftCardsResource:
    """Browse and manage gift cards."""

    def __init__(self, http: HttpClient):
        self._http = http

    def list(self) -> List[GiftCard]:
        """Get all available gift card products.

        Returns:
            List of GiftCard objects.
        """
        data = self._http.get("giftCards/list")
        items = data if isinstance(data, list) else data.get("results", [])
        return [GiftCard.from_dict(g) for g in items]


# ---------------------------------------------------------------------------
# Inserts
# ---------------------------------------------------------------------------

class InsertsResource:
    """Browse card inserts (business cards, flyers, etc.)."""

    def __init__(self, http: HttpClient):
        self._http = http

    def list(self) -> List[Insert]:
        """Get all available inserts.

        Returns:
            List of Insert objects.
        """
        data = self._http.get("inserts/list")
        items = data if isinstance(data, list) else data.get("results", [])
        return [Insert.from_dict(i) for i in items]


# ---------------------------------------------------------------------------
# QR Codes
# ---------------------------------------------------------------------------

class QRCodesResource:
    """Create, list, and manage QR codes.

    QR codes can be attached to custom cards via
    ``custom_cards.create(qr_code_id=...)``.

    Example::

        # Create a QR code
        qr = client.qr_codes.create(name="My QR", url="https://example.com")

        # Attach it to a custom card
        card = client.custom_cards.create(
            name="Card with QR",
            dimension_id=dims[0].id,
            cover_id=cover.id,
            qr_code_id=qr.id,
            qr_code_location="footer",
        )
    """

    def __init__(self, http: HttpClient):
        self._http = http

    def list(self) -> List[QRCode]:
        """Get all QR codes associated with your account.

        Returns:
            List of QRCode objects.
        """
        data = self._http.get("qrCodes/list")
        if isinstance(data, dict):
            items = data.get("list", data.get("results", []))
        elif isinstance(data, list):
            items = data
        else:
            items = []
        return [QRCode.from_dict(q) for q in items]

    def create(
        self,
        name: str,
        url: str,
        icon_id: Optional[int] = None,
        webhook_url: Optional[str] = None,
    ) -> QRCode:
        """Create a new QR code.

        Args:
            name: Display name for the QR code.
            url: The URL the QR code will point to.
            icon_id: Optional icon ID to overlay on the QR code.
            webhook_url: Optional webhook URL to receive scan notifications.

        Returns:
            QRCode object with the new ``id``.

        Example:
            >>> qr = client.qr_codes.create(
            ...     name="Website Link",
            ...     url="https://example.com",
            ... )
            >>> print(qr.id)
        """
        body: Dict[str, Any] = {"name": name, "url": url}
        if icon_id is not None:
            body["icon_id"] = icon_id
        if webhook_url is not None:
            body["webhook_url"] = webhook_url

        data = self._http.post("qrCode/", json_body=body)
        if isinstance(data, dict):
            # Response may have id at top level or nested
            if "id" in data and "url" not in data:
                return QRCode(id=str(data["id"]), url=url, title=name)
            return QRCode.from_dict(data)
        return QRCode(id="0", url=url, title=name)

    def delete(self, qr_code_id: int) -> Dict[str, Any]:
        """Delete a QR code.

        Args:
            qr_code_id: ID of the QR code to delete.
        """
        return self._http.delete(f"qrCode/{qr_code_id}/")

    def frames(self) -> List[Dict[str, Any]]:
        """Get available QR code frames.

        Frames are decorative borders placed around a QR code on the
        card.  Pass a frame ``id`` to ``custom_cards.create()`` via the
        ``qr_code_frame_id`` parameter.

        Returns:
            List of frame dicts with ``id``, ``type``, ``url``, and
            sizing info.

        Example:
            >>> frames = client.qr_codes.frames()
            >>> for f in frames:
            ...     print(f["id"], f["type"], f["url"])
        """
        data = self._http.get("qrCode/frames/")
        if isinstance(data, dict):
            return data.get("frames", [])
        return data if isinstance(data, list) else []


# ---------------------------------------------------------------------------
# Address Book
# ---------------------------------------------------------------------------

class AddressBookResource:
    """Manage saved addresses, countries, and states.

    Saved addresses are used with ``orders.send()`` by passing their IDs
    to the ``sender`` and ``recipient`` parameters.

    Example::

        # Save a sender (return address)
        sender_id = client.address_book.add_sender(
            first_name="David", last_name="Wachs",
            street1="100 S Mill Ave", city="Tempe", state="AZ", zip="85281",
        )

        # Save a recipient
        recipient_id = client.address_book.add_recipient(
            first_name="Jane", last_name="Doe",
            street1="123 Main St", city="Phoenix", state="AZ", zip="85001",
        )

        # Send using saved IDs
        client.orders.send(
            card_id="12345", font="hwDavid", message="Hello!",
            sender=sender_id, recipient=recipient_id,
        )
    """

    def __init__(self, http: HttpClient):
        self._http = http

    # -- Recipients (saved "to" addresses) ----------------------------------

    def list_recipients(self) -> List[SavedAddress]:
        """List saved recipient addresses.

        Returns:
            List of SavedAddress objects.

        Example:
            >>> recipients = client.address_book.list_recipients()
            >>> for r in recipients:
            ...     print(r.id, r)
        """
        data = self._http.get("profile/recipientsList")
        if isinstance(data, dict):
            items = data.get("addresses", [])
        elif isinstance(data, list):
            items = data
        else:
            items = []
        return [SavedAddress.from_dict(a) for a in items]

    def add_recipient(
        self,
        first_name: str,
        last_name: str,
        street1: str,
        city: str,
        state: str,
        zip: str,
        street2: Optional[str] = None,
        company: Optional[str] = None,
        country_id: Optional[str] = None,
        birthday: Optional[str] = None,
        anniversary: Optional[str] = None,
        allow_poor: Optional[bool] = None,
    ) -> int:
        """Save a new recipient address to the address book.

        Args:
            first_name: Recipient first name.
            last_name: Recipient last name.
            street1: Street address line 1.
            city: City.
            state: State/province code.
            zip: ZIP/postal code.
            street2: Street address line 2.
            company: Business/company name.
            country_id: Country ID (defaults to US).
            birthday: Birthday (e.g. ``"01/15/1990"``).
            anniversary: Anniversary date.
            allow_poor: Allow addresses with poor formatting.

        Returns:
            The saved address ID (``int``).

        Example:
            >>> rid = client.address_book.add_recipient(
            ...     first_name="Jane", last_name="Doe",
            ...     street1="123 Main St", city="Phoenix",
            ...     state="AZ", zip="85001",
            ... )
            >>> client.orders.send(..., recipient=rid)
        """
        body: Dict[str, Any] = {
            "first_name": first_name,
            "last_name": last_name,
            "address1": street1,
            "city": city,
            "state": state,
            "zip": zip,
        }
        if street2 is not None:
            body["address2"] = street2
        if company is not None:
            body["business_name"] = company
        if country_id is not None:
            body["country_id"] = country_id
        if birthday is not None:
            body["birthday"] = birthday
        if anniversary is not None:
            body["anniversary"] = anniversary
        if allow_poor is not None:
            body["allow_poor"] = allow_poor

        data = self._http.post("profile/addRecipient", json_body=body)
        if isinstance(data, dict):
            addr = data.get("address", data)
            return int(addr.get("id", addr.get("address_id", 0)))
        return 0

    def update_recipient(
        self,
        address_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        street1: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip: Optional[str] = None,
        street2: Optional[str] = None,
        company: Optional[str] = None,
        country_id: Optional[str] = None,
        birthday: Optional[str] = None,
        anniversary: Optional[str] = None,
        allow_poor: Optional[bool] = None,
    ) -> int:
        """Update an existing recipient address.

        Only the fields you pass will be updated; omitted fields remain
        unchanged.

        Args:
            address_id: ID of the recipient address to update.
            first_name: Recipient first name.
            last_name: Recipient last name.
            street1: Street address line 1.
            city: City.
            state: State/province code.
            zip: ZIP/postal code.
            street2: Street address line 2.
            company: Business/company name.
            country_id: Country ID.
            birthday: Birthday (e.g. ``"01/15/1990"``).
            anniversary: Anniversary date.
            allow_poor: Allow addresses with poor formatting.

        Returns:
            The address ID (``int``).

        Example:
            >>> client.address_book.update_recipient(
            ...     address_id=12345,
            ...     street1="456 New St",
            ...     city="Scottsdale",
            ... )
        """
        body: Dict[str, Any] = {"id": address_id}
        if first_name is not None:
            body["first_name"] = first_name
        if last_name is not None:
            body["last_name"] = last_name
        if street1 is not None:
            body["address1"] = street1
        if city is not None:
            body["city"] = city
        if state is not None:
            body["state"] = state
        if zip is not None:
            body["zip"] = zip
        if street2 is not None:
            body["address2"] = street2
        if company is not None:
            body["business_name"] = company
        if country_id is not None:
            body["country_id"] = country_id
        if birthday is not None:
            body["birthday"] = birthday
        if anniversary is not None:
            body["anniversary"] = anniversary
        if allow_poor is not None:
            body["allow_poor"] = allow_poor

        data = self._http.put("profile/updateRecipient", json_body=body)
        if isinstance(data, dict):
            addr = data.get("address", data)
            return int(addr.get("id", addr.get("address_id", address_id)))
        return address_id

    # -- Senders (saved return/"from" addresses) ----------------------------

    def list_senders(self) -> List[SavedAddress]:
        """List saved sender (return) addresses.

        Returns:
            List of SavedAddress objects.

        Example:
            >>> senders = client.address_book.list_senders()
            >>> for s in senders:
            ...     print(s.id, s)
        """
        data = self._http.get("profile/listAddresses")
        if isinstance(data, dict):
            # API response key has a typo ("addressses" with triple 's')
            items = data.get("addressses", data.get("addresses", []))
        elif isinstance(data, list):
            items = data
        else:
            items = []
        return [SavedAddress.from_dict(a) for a in items]

    def add_sender(
        self,
        first_name: str,
        last_name: str,
        street1: str,
        city: str,
        state: str,
        zip: str,
        street2: Optional[str] = None,
        company: Optional[str] = None,
        country_id: Optional[str] = None,
        default: Optional[bool] = None,
        allow_poor: Optional[bool] = None,
    ) -> int:
        """Save a new sender (return) address.

        Args:
            first_name: Sender first name.
            last_name: Sender last name.
            street1: Street address line 1.
            city: City.
            state: State/province code.
            zip: ZIP/postal code.
            street2: Street address line 2.
            company: Business/company name.
            country_id: Country ID (defaults to US).
            default: Set as the default return address.
            allow_poor: Allow addresses with poor formatting.

        Returns:
            The saved address ID (``int``).

        Example:
            >>> sid = client.address_book.add_sender(
            ...     first_name="David", last_name="Wachs",
            ...     street1="100 S Mill Ave", city="Tempe",
            ...     state="AZ", zip="85281",
            ... )
            >>> client.orders.send(..., sender=sid)
        """
        body: Dict[str, Any] = {
            "first_name": first_name,
            "last_name": last_name,
            "address1": street1,
            "city": city,
            "state": state,
            "zip": zip,
        }
        if street2 is not None:
            body["address2"] = street2
        if company is not None:
            body["business_name"] = company
        if country_id is not None:
            body["country_id"] = country_id
        if default is not None:
            body["default"] = default
        if allow_poor is not None:
            body["allow_poor"] = allow_poor

        data = self._http.post("profile/createAddress", json_body=body)
        if isinstance(data, dict):
            addr = data.get("address", data)
            return int(addr.get("id", addr.get("address_id", 0)))
        return 0

    # -- Countries and states -----------------------------------------------

    def countries(self) -> List[Country]:
        """Get all supported countries.

        Returns:
            List of Country objects.
        """
        data = self._http.get("countries/list")
        items = data if isinstance(data, list) else data.get("results", [])
        return [Country.from_dict(c) for c in items]

    def states(self, country_code: str = "US") -> List[State]:
        """Get states/provinces for a country.

        Args:
            country_code: ISO country code (default "US").

        Returns:
            List of State objects.
        """
        data = self._http.get("states/list", params={"country": country_code})
        items = data if isinstance(data, list) else data.get("results", [])
        return [State.from_dict(s) for s in items]


# ---------------------------------------------------------------------------
# Basket (multi-step order workflow)
# ---------------------------------------------------------------------------

class BasketResource:
    """Multi-step basket/cart workflow for complex orders.

    Workflow:
        1. Add one or more orders to the basket with ``add_order()``.
        2. Submit the basket for processing with ``send()``.
    """

    def __init__(self, http: HttpClient):
        self._http = http

    def add_order(
        self,
        card_id: str,
        message: Optional[str] = None,
        wishes: Optional[str] = None,
        font: Optional[str] = None,
        font_size: Optional[int] = None,
        auto_font_size: Optional[bool] = None,
        message_align: Optional[str] = None,
        addresses: Optional[List[Dict[str, Any]]] = None,
        address_ids: Optional[List[int]] = None,
        return_address_id: Optional[int] = None,
        denomination_id: Optional[int] = None,
        insert_id: Optional[int] = None,
        signature_id: Optional[int] = None,
        signature2_id: Optional[int] = None,
        date_send: Optional[str] = None,
        coupon_code: Optional[str] = None,
        check_quantity: Optional[bool] = None,
        check_quantity_inserts: Optional[bool] = None,
        delivery_confirmation: Optional[bool] = None,
        shipping_method_id: Optional[int] = None,
        shipping_rate_id: Optional[int] = None,
        shipping_address_id: Optional[int] = None,
        must_deliver_by: Optional[str] = None,
        client_metadata: Optional[str] = None,
        suppress_warnings: Optional[bool] = None,
        **extra: Any,
    ) -> Dict[str, Any]:
        """Add an order to the basket (``orders/placeBasket``).

        Provide recipients via **one** of:
        - ``addresses``: list of dicts with friendly keys (``firstName``,
          ``street1``, etc.) or raw ``to_*`` keys.  Friendly keys are
          auto-converted to ``to_*`` format.
        - ``address_ids``: list of saved address-book IDs.

        Args:
            card_id: ID of the card/stationery to use.
            message: The handwritten message body.
            wishes: Right-shifted closing part of the note.
            font: Font label (e.g. ``"hwDavid"``).
            font_size: Font size in points.
            auto_font_size: Enable automatic font sizing.
            message_align: Text alignment — ``"left"`` or ``"center"``.
            addresses: List of recipient address dicts.  Accepts
                camelCase keys (``firstName``, ``lastName``, ``street1``,
                ``city``, ``state``, ``zip``) which are auto-converted
                to the ``to_*`` format the API expects.  Raw ``to_*``
                keys are also accepted and passed through unchanged.
            address_ids: List of saved address IDs for recipients.
            return_address_id: Saved return-address ID.
            denomination_id: Gift card denomination ID.
            insert_id: Insert item ID.
            signature_id: Signature ID for the wishes section.
            signature2_id: Signature ID for the main message block.
            date_send: Scheduled send date.
            coupon_code: Promotional coupon code.
            check_quantity: Verify card stock availability.
            check_quantity_inserts: Verify insert stock availability.
            delivery_confirmation: Request delivery confirmation.
            shipping_method_id: Shipping method ID.
            shipping_rate_id: Shipping rate ID.
            shipping_address_id: Shipping address ID.
            must_deliver_by: Date the card must arrive by.
            client_metadata: Metadata string for tracking.
            suppress_warnings: Suppress warnings about unmatched merge
                fields in message/wishes.
            **extra: Any additional parameters the API accepts.

        Returns:
            Dict with ``order_id`` on success.

        Example:
            >>> client.basket.add_order(
            ...     card_id="3404",
            ...     message="Hello!",
            ...     font="hwDavid",
            ...     addresses=[{
            ...         "firstName": "Jane",
            ...         "lastName": "Doe",
            ...         "street1": "123 Main St",
            ...         "city": "Phoenix",
            ...         "state": "AZ",
            ...         "zip": "85001",
            ...     }],
            ... )
        """
        body: Dict[str, Any] = {"card_id": int(card_id)}

        if message is not None:
            body["message"] = message
        if wishes is not None:
            body["wishes"] = wishes
        if font is not None:
            body["font"] = font
        if font_size is not None:
            body["font_size"] = font_size
        if auto_font_size is not None:
            body["auto_font_size"] = auto_font_size
        if message_align is not None:
            body["message_align"] = message_align
        if addresses is not None:
            converted: List[Dict[str, Any]] = []
            for addr in addresses:
                if any(k.startswith("to_") for k in addr) or "address_id" in addr:
                    converted.append(addr)
                else:
                    addr = dict(addr)
                    row_message = addr.pop("message", None)
                    row_wishes = addr.pop("wishes", None)
                    row = _flatten_address(addr, "to")
                    if row_message is not None:
                        row["message"] = row_message
                    if row_wishes is not None:
                        row["wishes"] = row_wishes
                    converted.append(row)
            body["addresses"] = converted
        if address_ids is not None:
            body["address_ids"] = address_ids
        if return_address_id is not None:
            body["return_address_id"] = return_address_id
        if denomination_id is not None:
            body["denomination_id"] = denomination_id
        if insert_id is not None:
            body["insert_id"] = insert_id
        if signature_id is not None:
            body["signature_id"] = signature_id
        if signature2_id is not None:
            body["signature2_id"] = signature2_id
        if date_send is not None:
            body["date_send"] = date_send
        if coupon_code is not None:
            body["couponCode"] = coupon_code
        if check_quantity is not None:
            body["check_quantity"] = check_quantity
        if check_quantity_inserts is not None:
            body["check_quantity_inserts"] = check_quantity_inserts
        if delivery_confirmation is not None:
            body["delivery_confirmation"] = delivery_confirmation
        if shipping_method_id is not None:
            body["shipping_method_id"] = shipping_method_id
        if shipping_rate_id is not None:
            body["shipping_rate_id"] = shipping_rate_id
        if shipping_address_id is not None:
            body["shipping_address_id"] = shipping_address_id
        if must_deliver_by is not None:
            body["must_deliver_by"] = must_deliver_by
        if client_metadata is not None:
            body["client_metadata"] = client_metadata
        if suppress_warnings is not None:
            body["supressWarnings"] = suppress_warnings

        body.update(extra)

        return self._http.post("orders/placeBasket", json_body=body)

    def remove(self, basket_id: int) -> Dict[str, Any]:
        """Remove a single item from the basket.

        Args:
            basket_id: The basket item ID returned by ``add_order()``.

        Returns:
            Dict with ``status`` and remaining items.

        Example:
            >>> result = client.basket.add_order(card_id="100", ...)
            >>> basket_id = result["order_id"]
            >>> client.basket.remove(basket_id)
        """
        return self._http.post("basket/remove", json_body={"id": basket_id})

    def clear(self) -> Dict[str, Any]:
        """Remove all items from the basket.

        Returns:
            Dict with ``status``.
        """
        return self._http.post("basket/clear", json_body={})

    def list(self) -> Dict[str, Any]:
        """List all items currently in the basket.

        Returns:
            Dict with ``items`` list, ``totals``, and ``test_mode``.

        Example:
            >>> basket = client.basket.list()
            >>> for item in basket.get("items", []):
            ...     print(item["basket_id"], item["status"])
        """
        return self._http.get("basket/allNew")

    def get_item(self, basket_id: int) -> Dict[str, Any]:
        """Get a single basket item by ID.

        Args:
            basket_id: The basket item ID.

        Returns:
            Dict with basket item details.
        """
        return self._http.get("basket/item", params={"id": basket_id})

    def count(self) -> int:
        """Get the number of items currently in the basket.

        Returns:
            Integer count of basket items.
        """
        data = self._http.get("basket/count")
        if isinstance(data, dict):
            return int(data.get("count", 0))
        return 0

    def send(
        self,
        coupon_code: Optional[str] = None,
        credit_card_id: Optional[int] = None,
        test_mode: Optional[bool] = None,
        check_quantity: Optional[bool] = None,
        check_cass_before_submit: Optional[bool] = None,
        notes: Optional[Dict[str, str]] = None,
        price_structure: Optional[Dict[str, float]] = None,
        **extra: Any,
    ) -> Dict[str, Any]:
        """Submit the basket for processing (``basket/send``).

        Call this after adding orders with ``add_order()``.

        Args:
            coupon_code: Promotional coupon code.
            credit_card_id: ID of the credit card on file to charge.
            test_mode: If set, should match user's test_mode setting.
            check_quantity: Check stock; returns error if insufficient.
            check_cass_before_submit: Validate recipient address before
                submitting. If ``False``, address is checked after purchase
                and credits are refunded if invalid.
            notes: Dict mapping order IDs to note strings.
            price_structure: Expected payment breakdown with keys:
                coupon, credit1, credit2, money.
            **extra: Any additional parameters the API accepts.

        Returns:
            Order confirmation dict.
        """
        body: Dict[str, Any] = {}

        if coupon_code is not None:
            body["couponCode"] = coupon_code
        if credit_card_id is not None:
            body["credit_card_id"] = credit_card_id
        if test_mode is not None:
            body["test_mode"] = int(test_mode)
        if check_quantity is not None:
            body["check_quantity"] = check_quantity
        if check_cass_before_submit is not None:
            body["check_cass_before_submit"] = int(check_cass_before_submit)
        if notes is not None:
            body["notes"] = notes
        if price_structure is not None:
            body["price_structure"] = price_structure

        body.update(extra)

        return self._http.post("basket/send", json_body=body)


# ---------------------------------------------------------------------------
# Prospecting
# ---------------------------------------------------------------------------

class ProspectingResource:
    """Target prospecting endpoints."""

    def __init__(self, http: HttpClient):
        self._http = http

    def calculate_targets(
        self,
        zip_code: str,
        radius_miles: int = 10,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Calculate prospecting targets in an area.

        Args:
            zip_code: Center ZIP code.
            radius_miles: Search radius in miles.
            **kwargs: Additional filter parameters.

        Returns:
            Prospecting results dict.
        """
        body = {"zip": zip_code, "radius": radius_miles, **kwargs}
        return self._http.post("prospecting/calculateTargets", json_body=body)


_CAMEL_TO_API = {
    "firstName": "first_name",
    "lastName": "last_name",
    "street1": "address1",
    "street2": "address2",
    "company": "business_name",
    "city": "city",
    "state": "state",
    "zip": "zip",
    "country": "country",
}


def _flatten_address(data: Dict[str, Any], prefix: str) -> Dict[str, str]:
    """Flatten a camelCase address dict into ``prefix_field`` API fields."""
    result: Dict[str, str] = {}
    for key, value in data.items():
        if value is None:
            continue
        api_suffix = _CAMEL_TO_API.get(key, key)
        result[f"{prefix}_{api_suffix}"] = value
    return result


# ---------------------------------------------------------------------------
# Orders (the star of the show)
# ---------------------------------------------------------------------------

class OrdersResource:
    """Create and manage handwritten note orders.

    The ``send()`` convenience method uses the two-step workflow:
    ``orders/placeBasket`` → ``basket/send``.  For finer control, use
    ``client.basket.add_order()`` and ``client.basket.send()`` directly.
    """

    def __init__(self, http: HttpClient, basket: BasketResource):
        self._http = http
        self._basket = basket

    def send(
        self,
        card_id: str,
        font: str,
        recipient: Union[Recipient, Dict[str, Any], int, List[Union[Recipient, Dict[str, Any], int]]],
        message: Optional[str] = None,
        wishes: Optional[str] = None,
        sender: Union[Sender, Dict[str, Any], int, None] = None,
        return_address_id: Optional[int] = None,
        message_align: Optional[str] = None,
        denomination_id: Optional[int] = None,
        insert_id: Optional[int] = None,
        credit_card_id: Optional[int] = None,
        coupon_code: Optional[str] = None,
        date_send: Optional[str] = None,
        check_cass_before_submit: Optional[bool] = None,
        delivery_confirmation: Optional[bool] = None,
        client_metadata: Optional[str] = None,
        suppress_warnings: Optional[bool] = None,
        signature_id: Optional[int] = None,
        signature2_id: Optional[int] = None,
        font_size: Optional[int] = None,
        auto_font_size: Optional[bool] = None,
        **extra: Any,
    ) -> Dict[str, Any]:
        """Send a handwritten note — adds to basket then sends in one call.

        Uses ``orders/placeBasket`` + ``basket/send`` under the hood.

        The ``recipient`` can be:
        - A ``Recipient`` object.
        - A dict with camelCase keys (``firstName``, ``street1``, etc.).
        - A dict already in ``to_*`` format (``to_first_name``, etc.).
        - An ``int`` saved address ID.
        - A **list** of any of the above for bulk orders.

        The ``sender`` (return address) can be:
        - A ``Sender`` object.
        - A dict with camelCase keys (``firstName``, ``street1``, etc.).
        - An ``int`` saved address ID.

        Each recipient dict may include ``"message"``, ``"wishes"``, and
        ``"sender"`` keys for per-recipient overrides.  The top-level
        parameters serve as defaults for any recipient that doesn't specify
        its own.

        Args:
            card_id: ID of the card/stationery to use.
            font: Handwriting font ID (e.g. ``"hwDavid"``).
            recipient: Recipient address(es) — see above for formats.
            message: Default message body applied to recipients that don't
                include their own ``"message"`` key.
            wishes: Default closing/wishes applied to recipients that don't
                include their own ``"wishes"`` key.
            sender: Default return address — ``Sender`` object, dict, or
                saved address ID.  Can be overridden per-recipient.
            return_address_id: Saved return-address ID (alias for
                ``sender=<int>``; ``sender`` takes precedence).
            message_align: Text alignment — ``"left"`` or ``"center"``.
            denomination_id: Gift card denomination ID.
            insert_id: Insert item ID.
            credit_card_id: Credit card on file to charge.
            coupon_code: Promotional coupon code.
            date_send: Scheduled send date.
            check_cass_before_submit: Validate recipient address before
                submitting.
            delivery_confirmation: Request delivery confirmation.
            client_metadata: Metadata string for tracking.
            suppress_warnings: Suppress merge-field warnings.
            signature_id: Signature ID for the wishes section.
            signature2_id: Signature ID for the main message block.
            font_size: Font size in points.
            auto_font_size: Enable automatic font sizing.
            **extra: Additional parameters passed to ``placeBasket``.

        Returns:
            Dict with order confirmation from ``basket/send``.

        Examples:
            Single recipient with sender::

                client.orders.send(
                    card_id="12345",
                    font="hwDavid",
                    message="Thank you!",
                    sender={"firstName": "David", "lastName": "Wachs",
                            "street1": "100 S Mill Ave", "city": "Tempe",
                            "state": "AZ", "zip": "85281"},
                    recipient={"firstName": "Jane", "lastName": "Doe",
                               "street1": "123 Main St", "city": "Phoenix",
                               "state": "AZ", "zip": "85001"},
                )

            Using saved address IDs::

                client.orders.send(
                    card_id="12345",
                    font="hwDavid",
                    message="Thank you!",
                    sender=98765,      # saved return-address ID
                    recipient=67890,   # saved recipient address ID
                )

            Per-recipient sender and message overrides::

                client.orders.send(
                    card_id="12345",
                    font="hwDavid",
                    message="Default message",
                    sender={"firstName": "David", ...},
                    recipient=[
                        {
                            "firstName": "Jane", "lastName": "Doe",
                            "street1": "123 Main St", "city": "Phoenix",
                            "state": "AZ", "zip": "85001",
                            "message": "Thanks Jane!",
                            "sender": {"firstName": "Other", ...},
                        },
                        67890,  # saved address ID, uses default sender
                    ],
                )
        """
        # -- Resolve sender ----------------------------------------------------
        # int → return_address_id, Sender/dict → from_* fields per row
        sender_id: Optional[int] = return_address_id
        default_sender_fields: Optional[Dict[str, str]] = None

        if sender is not None:
            if isinstance(sender, int):
                sender_id = sender
            else:
                if isinstance(sender, Sender):
                    sender = sender.to_dict()
                default_sender_fields = _flatten_address(sender, "from")

        # -- Resolve recipients ------------------------------------------------
        if not isinstance(recipient, list):
            recipient = [recipient]

        addresses: List[Dict[str, Any]] = []
        for r in recipient:
            row: Dict[str, Any] = {}

            if isinstance(r, int):
                # Saved address ID
                row["address_id"] = r
            elif isinstance(r, Recipient):
                row = _flatten_address(r.to_dict(), "to")
            elif isinstance(r, dict):
                # Pull out per-row overrides before flattening
                r = dict(r)  # shallow copy to avoid mutating caller's dict
                row_message = r.pop("message", None)
                row_wishes = r.pop("wishes", None)
                row_sender = r.pop("sender", None)

                # Flatten recipient address
                if not any(k.startswith("to_") for k in r):
                    row = _flatten_address(r, "to")
                else:
                    row = r

                if row_message is not None:
                    row["message"] = row_message
                if row_wishes is not None:
                    row["wishes"] = row_wishes

                # Per-recipient sender override
                if row_sender is not None:
                    if isinstance(row_sender, int):
                        row["return_address_id"] = row_sender
                    else:
                        if isinstance(row_sender, Sender):
                            row_sender = row_sender.to_dict()
                        row.update(_flatten_address(row_sender, "from"))
            else:
                raise TypeError(
                    "Each recipient must be a Recipient, dict, or int"
                )

            # Apply defaults for message/wishes if not already set
            if "message" not in row and message is not None:
                row["message"] = message
            if "wishes" not in row and wishes is not None:
                row["wishes"] = wishes

            # Apply default sender from_* fields if no per-row sender
            if (
                default_sender_fields is not None
                and not any(k.startswith("from_") for k in row)
                and "return_address_id" not in row
            ):
                row.update(default_sender_fields)

            addresses.append(row)

        # Build placeBasket kwargs
        place_kwargs: Dict[str, Any] = {
            "card_id": card_id,
            "font": font,
            "addresses": addresses,
        }
        if sender_id is not None:
            place_kwargs["return_address_id"] = sender_id
        if message_align is not None:
            place_kwargs["message_align"] = message_align
        if denomination_id is not None:
            place_kwargs["denomination_id"] = denomination_id
        if insert_id is not None:
            place_kwargs["insert_id"] = insert_id
        if date_send is not None:
            place_kwargs["date_send"] = date_send
        if delivery_confirmation is not None:
            place_kwargs["delivery_confirmation"] = delivery_confirmation
        if client_metadata is not None:
            place_kwargs["client_metadata"] = client_metadata
        if suppress_warnings is not None:
            place_kwargs["suppress_warnings"] = suppress_warnings
        if signature_id is not None:
            place_kwargs["signature_id"] = signature_id
        if signature2_id is not None:
            place_kwargs["signature2_id"] = signature2_id
        if font_size is not None:
            place_kwargs["font_size"] = font_size
        if auto_font_size is not None:
            place_kwargs["auto_font_size"] = auto_font_size
        if coupon_code is not None:
            place_kwargs["coupon_code"] = coupon_code

        place_kwargs.update(extra)

        # Step 1: placeBasket
        self._basket.add_order(**place_kwargs)

        # Step 2: basket/send
        send_kwargs: Dict[str, Any] = {}
        if credit_card_id is not None:
            send_kwargs["credit_card_id"] = credit_card_id
        if coupon_code is not None:
            send_kwargs["coupon_code"] = coupon_code
        if check_cass_before_submit is not None:
            send_kwargs["check_cass_before_submit"] = check_cass_before_submit

        return self._basket.send(**send_kwargs)

    def get(self, order_id: str) -> Order:
        """Retrieve an order by ID.

        Args:
            order_id: The order's unique identifier.

        Returns:
            Order object with current status.
        """
        data = self._http.get(f"orders/get/{order_id}")
        return Order.from_dict(data if isinstance(data, dict) else {})

    def list(
        self,
        page: int = 1,
        per_page: int = 50,
    ) -> List[Order]:
        """List orders with pagination.

        Args:
            page: Page number (1-indexed).
            per_page: Results per page.

        Returns:
            List of Order objects.
        """
        data = self._http.get(
            "orders/list",
            params={"page": page, "per_page": per_page},
        )
        items = data if isinstance(data, list) else data.get("results", data.get("orders", []))
        return [Order.from_dict(o) for o in items]
