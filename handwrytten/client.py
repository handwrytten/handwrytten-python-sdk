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
    ShippingResource,
)


class Handwrytten:
    """Handwrytten API client.

    The primary interface for interacting with the Handwrytten API. Provides
    access to all API resources as convenient, namespaced attributes.

    Args:
        api_key: Your Handwrytten API key (legacy auth). Provide either
            ``api_key`` or ``access_token``. Obtain an API key from
            https://app.handwrytten.com/api-keys
        access_token: OAuth2 access token (Bearer auth). Provide either
            ``api_key`` or ``access_token``.
        base_url: Override the API base URL (default: production).
        timeout: Request timeout in seconds.
        max_retries: Number of automatic retries for transient errors.
        session: Optional ``requests.Session`` for connection pooling
            or custom transport adapters.

    Example:
        >>> from handwrytten import Handwrytten
        >>> client = Handwrytten("your_api_key_here")
        >>>
        >>> # Or with an OAuth access token:
        >>> client = Handwrytten(access_token="oauth_token_here")
        >>>
        >>> # Check your account
        >>> user = client.auth.get_user()
        >>> print(f"Logged in as {user.email}")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = 3,
        session: Optional[requests.Session] = None,
    ):
        if not api_key and not access_token:
            raise ValueError(
                "An API key or access token is required. "
                "Get an API key at https://app.handwrytten.com/api-keys"
            )

        self._http = HttpClient(
            api_key=api_key,
            access_token=access_token,
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
        self.shipping = ShippingResource(self._http)
        self.basket = BasketResource(self._http)
        self.orders = OrdersResource(self._http, self.basket)
        self.prospecting = ProspectingResource(self._http)

    def __repr__(self) -> str:
        if self._http.access_token:
            masked = self._http.access_token[:8] + "..."
            return f"Handwrytten(access_token='{masked}')"
        masked = self._http.api_key[:8] + "..." if self._http.api_key else "None"
        return f"Handwrytten(api_key='{masked}')"
