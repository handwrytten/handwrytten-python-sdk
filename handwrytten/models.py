"""Data models for Handwrytten API responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _to_float(value: Any) -> float | None:
    """Coerce API numerics (ints, floats, numeric strings) to float.

    Returns None when the value is absent, empty or not numeric.
    """
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any, default: int = 0) -> int:
    """Coerce API identifiers to int, falling back to ``default`` when absent or invalid."""
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass
class User:
    """Authenticated user profile."""

    id: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    credits: float | None = None
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> User:
        return cls(
            id=str(data.get("id", data.get("uid", ""))),
            email=data.get("email"),
            first_name=data.get("first_name") or data.get("firstName"),
            last_name=data.get("last_name") or data.get("lastName"),
            company=data.get("company"),
            credits=_to_float(data.get("credits")),
            raw=data,
        )


@dataclass
class Card:
    """A card/stationery template."""

    id: str
    title: str
    image_url: str | None = None
    category: str | None = None
    cover: str | None = None
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> Card:
        return cls(
            id=str(data.get("id", "")),
            title=data.get("title", data.get("name", "")),
            image_url=data.get("image_url") or data.get("image") or data.get("cover"),
            category=data.get("category") or data.get("product_type"),
            cover=data.get("cover"),
            raw=data,
        )


@dataclass
class Font:
    """A handwriting font/style."""

    id: str
    name: str
    label: str
    preview_url: str | None = None
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> Font:
        return cls(
            id=str(data.get("id", "")),
            name=data.get("name", data.get("title", "")),
            label=data.get("label", data.get("name", "")),
            preview_url=data.get("preview_url") or data.get("image") or data.get("preview"),
            raw=data,
        )


@dataclass
class Denomination:
    """A gift card denomination (price point)."""

    id: int
    nominal: float
    price: float
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> Denomination:
        return cls(
            id=int(data.get("id", 0)),
            nominal=float(data.get("nominal", 0)),
            price=float(data.get("price", 0)),
            raw=data,
        )


@dataclass
class GiftCard:
    """A gift card product."""

    id: str
    title: str
    amount: float | None = None
    image_url: str | None = None
    denominations: list[Denomination] = field(default_factory=list)
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> GiftCard:
        amount = data.get("amount")
        if amount is None:
            amount = data.get("value")
        denoms_raw = data.get("denominations", [])
        denoms = (
            [Denomination.from_dict(d) for d in denoms_raw]
            if isinstance(denoms_raw, list)
            else []
        )
        return cls(
            id=str(data.get("id", "")),
            title=data.get("title", data.get("name", "")),
            amount=_to_float(amount),
            image_url=data.get("image_url") or data.get("image"),
            denominations=denoms,
            raw=data,
        )


@dataclass
class Insert:
    """A card insert (e.g. business card, flyer)."""

    id: str
    title: str
    image_url: str | None = None
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> Insert:
        return cls(
            id=str(data.get("id", "")),
            title=data.get("title", data.get("name", "")),
            image_url=data.get("image_url") or data.get("image"),
            raw=data,
        )


class ZoneType:
    """Content type for a custom card zone (header, main, footer, back)."""

    TEXT = "text"
    LOGO = "logo"
    COVER = "cover"  # back zone only


class QRCodeLocation:
    """Valid locations for placing a QR code on a custom card."""

    HEADER = "header"
    FOOTER = "footer"
    MAIN = "main"


class DeliveryConfirmation:
    """Values for the ``delivery_confirmation`` order parameter.

    The API accepts an integer ``0``–``2``. Booleans remain backward
    compatible: ``False`` → ``NONE``, ``True`` → ``CONFIRMATION``.
    """

    NONE = 0
    CONFIRMATION = 1
    CASS_ONLY = 2
    # Aliases shared with the JavaScript SDK; existing names remain supported.
    DELIVERY_CONFIRMATION = CONFIRMATION
    CASS_VALIDATION = CASS_ONLY


@dataclass
class QRCode:
    """A QR code attachment."""

    id: str
    url: str | None = None
    title: str | None = None
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> QRCode:
        return cls(
            id=str(data.get("id", "")),
            url=data.get("url"),
            title=data.get("title") or data.get("name"),
            raw=data,
        )


@dataclass
class Recipient:
    """A mail recipient address."""

    first_name: str
    last_name: str
    street1: str
    city: str
    state: str
    zip: str
    street2: str | None = None
    company: str | None = None
    country: str = "US"

    def to_dict(self) -> dict:
        d = {
            "firstName": self.first_name,
            "lastName": self.last_name,
            "street1": self.street1,
            "city": self.city,
            "state": self.state,
            "zip": self.zip,
            "country": self.country,
        }
        if self.street2:
            d["street2"] = self.street2
        if self.company:
            d["company"] = self.company
        return d


@dataclass
class Sender:
    """A return address."""

    first_name: str
    last_name: str
    street1: str
    city: str
    state: str
    zip: str
    street2: str | None = None
    company: str | None = None
    country: str = "US"

    def to_dict(self) -> dict:
        d = {
            "firstName": self.first_name,
            "lastName": self.last_name,
            "street1": self.street1,
            "city": self.city,
            "state": self.state,
            "zip": self.zip,
            "country": self.country,
        }
        if self.street2:
            d["street2"] = self.street2
        if self.company:
            d["company"] = self.company
        return d


@dataclass
class Order:
    """An order for a handwritten card."""

    id: str
    status: str | None = None
    message: str | None = None
    card_id: str | None = None
    font_id: str | None = None
    created_at: str | None = None
    tracking_number: str | None = None
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> Order:
        return cls(
            id=str(data.get("id", data.get("order_id", ""))),
            status=data.get("status"),
            message=data.get("message"),
            card_id=str(data.get("card_id", "")) if data.get("card_id") else None,
            font_id=str(data.get("font_id", "")) if data.get("font_id") else None,
            created_at=data.get("created_at") or data.get("createdAt"),
            tracking_number=data.get("tracking_number") or data.get("trackingNumber"),
            raw=data,
        )


@dataclass
class Dimension:
    """A card dimension for custom card creation."""

    id: int
    orientation: str
    format: str
    open_width: str
    open_height: str
    name: str | None = None
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> Dimension:
        return cls(
            id=int(data.get("id", 0)),
            orientation=data.get("orientation", ""),
            format=data.get("format", ""),
            open_width=data.get("open_width", ""),
            open_height=data.get("open_height", ""),
            name=data.get("name"),
            raw=data,
        )

    def __str__(self) -> str:
        return f"{self.open_width}x{self.open_height} {self.format} ({self.orientation})"


@dataclass
class CustomImage:
    """An uploaded image for custom card designs."""

    id: int
    image_url: str | None = None
    image_type: str | None = None
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> CustomImage:
        return cls(
            id=int(data.get("id", 0)),
            image_url=data.get("src") or data.get("image_url") or data.get("url"),
            image_type=data.get("type"),
            raw=data,
        )


@dataclass
class CustomCard:
    """A custom card created from uploaded images."""

    card_id: int
    category_id: int | None = None
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> CustomCard:
        return cls(
            card_id=int(data.get("card_id", data.get("id", 0))),
            category_id=int(data["category_id"]) if data.get("category_id") else None,
            raw=data,
        )


@dataclass
class SavedAddress:
    """A saved address from the user's address book (recipient or sender)."""

    id: int
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    street1: str | None = None
    street2: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    country: str | None = None
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> SavedAddress:
        return cls(
            id=int(data.get("id", 0)),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            company=data.get("business_name"),
            street1=data.get("address1"),
            street2=data.get("address2"),
            city=data.get("city"),
            state=data.get("state") or data.get("states"),
            zip=str(data.get("zip", "")),
            country=data.get("country"),
            raw=data,
        )

    def __str__(self) -> str:
        name = " ".join(filter(None, [self.first_name, self.last_name]))
        return f"{name}, {self.street1}, {self.city}, {self.state} {self.zip}"


@dataclass
class Signature:
    """A saved handwriting signature."""

    id: int
    preview: str | None = None
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> Signature:
        return cls(
            id=int(data.get("id", 0)),
            preview=data.get("preview"),
            raw=data,
        )


@dataclass
class Country:
    """A supported country, including postage and alternate names."""

    code: str
    name: str
    raw: dict = field(default_factory=dict, repr=False)
    id: int = 0
    aliases: list[str] = field(default_factory=list)
    delivery_cost: float = 0.0

    @classmethod
    def from_dict(cls, data: dict) -> Country:
        cost = _to_float(data.get("delivery_cost", data.get("deliveryCost")))
        code = data.get("ups_code")
        if code is None:
            code = data.get("code")
        return cls(
            id=_to_int(data.get("id")),
            code=str(code) if code is not None else "",
            name=data.get("name", ""),
            aliases=[alias.strip() for alias in (data.get("aliases") or "").split("|") if alias.strip()],
            delivery_cost=cost if cost is not None else 0.0,
            raw=data,
        )


@dataclass
class State:
    """A state/province."""

    code: str
    name: str
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> State:
        return cls(
            code=data.get("code") or data.get("abbreviation") or data.get("short_name") or "",
            name=data.get("name", ""),
            raw=data,
        )


@dataclass
class StampOption:
    """A postal stamp option (e.g. First Class, Presorted).

    Pass the ``id`` to ``orders.send()`` / ``basket.add_order()`` via the
    ``stamp_option_id`` parameter. Applies to US mail; ignored for
    international.
    """

    id: int
    name: str
    description: str | None = None
    price: float | None = None
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> StampOption:
        price = data.get("price")
        return cls(
            id=int(data.get("id", 0)),
            name=data.get("name", data.get("title", data.get("label", ""))),
            description=data.get("description"),
            price=float(price) if price is not None else None,
            raw=data,
        )
