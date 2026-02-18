"""Data models for Handwrytten API responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class User:
    """Authenticated user profile."""

    id: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    credits: Optional[float] = None
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(
            id=str(data.get("id", data.get("uid", ""))),
            email=data.get("email"),
            first_name=data.get("first_name") or data.get("firstName"),
            last_name=data.get("last_name") or data.get("lastName"),
            company=data.get("company"),
            credits=data.get("credits"),
            raw=data,
        )


@dataclass
class Card:
    """A card/stationery template."""

    id: str
    title: str
    image_url: Optional[str] = None
    category: Optional[str] = None
    cover: Optional[str] = None
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> "Card":
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
    preview_url: Optional[str] = None
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> "Font":
        return cls(
            id=str(data.get("id", "")),
            name=data.get("name", data.get("title", "")),
            label=data.get("label", data.get("name", "")),
            preview_url=data.get("preview_url") or data.get("image") or data.get("preview"),
            raw=data,
        )


@dataclass
class GiftCard:
    """A gift card product."""

    id: str
    title: str
    amount: Optional[float] = None
    image_url: Optional[str] = None
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> "GiftCard":
        return cls(
            id=str(data.get("id", "")),
            title=data.get("title", data.get("name", "")),
            amount=data.get("amount") or data.get("value"),
            image_url=data.get("image_url") or data.get("image"),
            raw=data,
        )


@dataclass
class Insert:
    """A card insert (e.g. business card, flyer)."""

    id: str
    title: str
    image_url: Optional[str] = None
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> "Insert":
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


@dataclass
class QRCode:
    """A QR code attachment."""

    id: str
    url: Optional[str] = None
    title: Optional[str] = None
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> "QRCode":
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
    street2: Optional[str] = None
    company: Optional[str] = None
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
    street2: Optional[str] = None
    company: Optional[str] = None
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
    status: Optional[str] = None
    message: Optional[str] = None
    card_id: Optional[str] = None
    font_id: Optional[str] = None
    created_at: Optional[str] = None
    tracking_number: Optional[str] = None
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> "Order":
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
    name: Optional[str] = None
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> "Dimension":
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
    image_url: Optional[str] = None
    image_type: Optional[str] = None
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> "CustomImage":
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
    category_id: Optional[int] = None
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> "CustomCard":
        return cls(
            card_id=int(data.get("card_id", data.get("id", 0))),
            category_id=int(data["category_id"]) if data.get("category_id") else None,
            raw=data,
        )


@dataclass
class SavedAddress:
    """A saved address from the user's address book (recipient or sender)."""

    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    street1: Optional[str] = None
    street2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> "SavedAddress":
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
class Country:
    """A supported country."""

    code: str
    name: str
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> "Country":
        return cls(
            code=data.get("code", data.get("id", "")),
            name=data.get("name", ""),
            raw=data,
        )


@dataclass
class State:
    """A state/province."""

    code: str
    name: str
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> "State":
        return cls(
            code=data.get("code", data.get("abbreviation", "")),
            name=data.get("name", ""),
            raw=data,
        )
