"""Main Handwrytten client — the single entry point for all API interactions."""

from __future__ import annotations

from typing import Optional

import requests

from handwrytten.http_client import DEFAULT_BASE_URL, DEFAULT_TIMEOUT, HttpClient
from handwrytten.resources import (
    AddressBookResource,
    AuthResource,
    BasketResource,
    CardsResource,
    CustomCardsResource,
    FontsResource,
    GiftCardsResource,
    InsertsResource,
    OrdersResource,
    ProspectingResource,
    QRCodesResource,
)


class Handwrytten:
    """Handwrytten API client.

    The primary interface for interacting with the Handwrytten API. Provides
    access to all API resources as convenient, namespaced attributes.

    Args:
        api_key: Your Handwrytten API key. Obtain one from
            https://app.handwrytten.com/api-keys
        base_url: Override the API base URL (default: production).
        timeout: Request timeout in seconds.
        max_retries: Number of automatic retries for transient errors.
        session: Optional ``requests.Session`` for connection pooling
            or custom transport adapters.

    Example:
        >>> from handwrytten import Handwrytten
        >>> client = Handwrytten("your_api_key_here")
        >>>
        >>> # Check your account
        >>> user = client.auth.get_user()
        >>> print(f"Logged in as {user.email}")
        >>>
        >>> # Browse available cards and fonts
        >>> cards = client.cards.list()
        >>> fonts = client.fonts.list()
        >>>
        >>> # Send a handwritten note
        >>> result = client.orders.send(
        ...     card_id=cards[0].id,
        ...     message="Thanks for being an amazing customer!",
        ...     font=fonts[0].label,
        ...     recipient={
        ...         "firstName": "Jane",
        ...         "lastName": "Doe",
        ...         "street1": "123 Main Street",
        ...         "city": "Phoenix",
        ...         "state": "AZ",
        ...         "zip": "85001",
        ...     },
        ... )
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = 3,
        session: Optional[requests.Session] = None,
    ):
        if not api_key:
            raise ValueError(
                "An API key is required. Get one at https://app.handwrytten.com/api-keys"
            )

        self._http = HttpClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            session=session,
        )

        # Resource namespaces
        self.auth = AuthResource(self._http)
        self.cards = CardsResource(self._http)
        self.custom_cards = CustomCardsResource(self._http)
        self.fonts = FontsResource(self._http)
        self.gift_cards = GiftCardsResource(self._http)
        self.inserts = InsertsResource(self._http)
        self.qr_codes = QRCodesResource(self._http)
        self.address_book = AddressBookResource(self._http)
        self.basket = BasketResource(self._http)
        self.orders = OrdersResource(self._http, self.basket)
        self.prospecting = ProspectingResource(self._http)

    def __repr__(self) -> str:
        masked = self._http.api_key[:8] + "..." if self._http.api_key else "None"
        return f"Handwrytten(api_key='{masked}')"
