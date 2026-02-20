from __future__ import annotations

from typing import Any

import httpx

from truelist._http import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    build_client_kwargs,
    sync_request,
)
from truelist.types import AccountInfo, ValidationResult


class EmailResource:
    """Sync resource for email validation operations."""

    def __init__(self, client: httpx.Client, max_retries: int) -> None:
        self._client = client
        self._max_retries = max_retries

    def validate(self, email: str) -> ValidationResult:
        """Validate an email address using server-side verification.

        Args:
            email: The email address to validate.

        Returns:
            A ValidationResult with the verification details.
        """
        response = sync_request(
            self._client,
            "POST",
            "/api/v1/verify",
            max_retries=self._max_retries,
            json={"email": email},
        )
        return _parse_validation_result(response.json())

    def form_validate(self, email: str) -> ValidationResult:
        """Validate an email address using form/frontend verification.

        This endpoint has different rate limits suited for frontend form validation.

        Args:
            email: The email address to validate.

        Returns:
            A ValidationResult with the verification details.
        """
        response = sync_request(
            self._client,
            "POST",
            "/api/v1/form_verify",
            max_retries=self._max_retries,
            json={"email": email},
        )
        return _parse_validation_result(response.json())


class AccountResource:
    """Sync resource for account operations."""

    def __init__(self, client: httpx.Client, max_retries: int) -> None:
        self._client = client
        self._max_retries = max_retries

    def get(self) -> AccountInfo:
        """Get account information for the authenticated user.

        Returns:
            An AccountInfo with email, plan, and credits.
        """
        response = sync_request(
            self._client,
            "GET",
            "/api/v1/account",
            max_retries=self._max_retries,
        )
        data: dict[str, Any] = response.json()
        return AccountInfo(
            email=data["email"],
            plan=data["plan"],
            credits=data["credits"],
        )


class Truelist:
    """Synchronous client for the Truelist email validation API.

    Usage::

        client = Truelist("your-api-key")
        result = client.email.validate("user@example.com")
        print(result.is_valid)

    Or as a context manager::

        with Truelist("your-api-key") as client:
            result = client.email.validate("user@example.com")
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        self._max_retries = max_retries
        self._client = httpx.Client(
            **build_client_kwargs(api_key=api_key, base_url=base_url, timeout=timeout)
        )
        self._email: EmailResource | None = None
        self._account: AccountResource | None = None

    @property
    def email(self) -> EmailResource:
        """Access email validation operations."""
        if self._email is None:
            self._email = EmailResource(self._client, self._max_retries)
        return self._email

    @property
    def account(self) -> AccountResource:
        """Access account operations."""
        if self._account is None:
            self._account = AccountResource(self._client, self._max_retries)
        return self._account

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> Truelist:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


def _parse_validation_result(data: dict[str, Any]) -> ValidationResult:
    return ValidationResult(
        email=data["email"],
        state=data["state"],
        sub_state=data["sub_state"],
        free_email=data["free_email"],
        role=data["role"],
        disposable=data["disposable"],
        suggestion=data.get("suggestion"),
    )
