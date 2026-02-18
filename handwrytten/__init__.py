"""
Handwrytten Python SDK
~~~~~~~~~~~~~~~~~~~~~~

Official Python SDK for the Handwrytten API - send real handwritten notes
at scale using robots with real pens.

Usage:
    >>> from handwrytten import Handwrytten
    >>> client = Handwrytten("your_api_key")
    >>> cards = client.cards.list()
    >>> fonts = client.fonts.list()
    >>> client.orders.send(
    ...     card_id=cards[0].id,
    ...     font=fonts[0].id,
    ...     message="Thanks for your business!",
    ...     recipient={"firstName": "Jane", "lastName": "Doe", ...},
    ... )
"""

__version__ = "1.1.0"

from handwrytten.client import Handwrytten
from handwrytten.exceptions import (
    HandwryttenError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    RateLimitError,
    ServerError,
)
from handwrytten.models import (
    Card,
    CustomCard,
    CustomImage,
    Dimension,
    Font,
    GiftCard,
    Insert,
    Order,
    QRCode,
    QRCodeLocation,
    Recipient,
    SavedAddress,
    Sender,
    Country,
    State,
    User,
    ZoneType,
)

__all__ = [
    "Handwrytten",
    "HandwryttenError",
    "AuthenticationError",
    "BadRequestError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "Card",
    "CustomCard",
    "CustomImage",
    "Dimension",
    "Font",
    "GiftCard",
    "Insert",
    "Order",
    "QRCode",
    "QRCodeLocation",
    "Recipient",
    "SavedAddress",
    "Sender",
    "Country",
    "State",
    "User",
    "ZoneType",
]
