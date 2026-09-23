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

from handwrytten._version import __version__
from handwrytten.client import Handwrytten
from handwrytten.exceptions import (
    AuthenticationError,
    BadRequestError,
    HandwryttenError,
    NotFoundError,
    RateLimitError,
    ServerError,
)
from handwrytten.models import (
    Card,
    Country,
    CustomCard,
    CustomImage,
    DeliveryConfirmation,
    Denomination,
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
    Signature,
    StampOption,
    State,
    User,
    ZoneType,
)

__all__ = [
    "AuthenticationError",
    "BadRequestError",
    "Card",
    "Country",
    "CustomCard",
    "CustomImage",
    "DeliveryConfirmation",
    "Denomination",
    "Dimension",
    "Font",
    "GiftCard",
    "Handwrytten",
    "HandwryttenError",
    "Insert",
    "NotFoundError",
    "Order",
    "QRCode",
    "QRCodeLocation",
    "RateLimitError",
    "Recipient",
    "SavedAddress",
    "Sender",
    "ServerError",
    "Signature",
    "StampOption",
    "State",
    "User",
    "ZoneType",
    "__version__",
]
