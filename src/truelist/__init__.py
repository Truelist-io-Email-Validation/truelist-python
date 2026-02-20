"""Truelist - Official Python SDK for the Truelist.io email validation API."""

from truelist._version import __version__
from truelist.async_client import AsyncTruelist
from truelist.client import Truelist
from truelist.errors import (
    ApiError,
    AuthenticationError,
    ConnectionError,
    RateLimitError,
    TimeoutError,
    TruelistError,
)
from truelist.types import AccountInfo, ValidationResult

__all__ = [
    "__version__",
    "AccountInfo",
    "ApiError",
    "AsyncTruelist",
    "AuthenticationError",
    "ConnectionError",
    "RateLimitError",
    "TimeoutError",
    "Truelist",
    "TruelistError",
    "ValidationResult",
]
