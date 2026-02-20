from __future__ import annotations


class TruelistError(Exception):
    """Base exception for all Truelist SDK errors."""

    message: str

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ApiError(TruelistError):
    """Error returned by the Truelist API."""

    status_code: int
    body: str | None

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        body: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(message)

    def __repr__(self) -> str:
        return f"ApiError(status_code={self.status_code}, message={self.message!r})"


class AuthenticationError(ApiError):
    """Raised when the API key is invalid or missing (HTTP 401/403)."""

    def __init__(
        self,
        message: str = "Invalid or missing API key",
        *,
        status_code: int = 401,
        body: str | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, body=body)


class RateLimitError(ApiError):
    """Raised when the API rate limit is exceeded (HTTP 429)."""

    retry_after: float | None

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        status_code: int = 429,
        body: str | None = None,
        retry_after: float | None = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message, status_code=status_code, body=body)


class ConnectionError(TruelistError):
    """Raised when a connection to the API cannot be established."""

    def __init__(self, message: str = "Failed to connect to the Truelist API") -> None:
        super().__init__(message)


class TimeoutError(TruelistError):
    """Raised when a request to the API times out."""

    def __init__(self, message: str = "Request to the Truelist API timed out") -> None:
        super().__init__(message)
