from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationResult:
    """Result of an email validation request."""

    email: str
    state: str
    sub_state: str
    free_email: bool
    role: bool
    disposable: bool
    suggestion: str | None

    @property
    def is_valid(self) -> bool:
        """Whether the email state is 'valid'."""
        return self.state == "valid"

    @property
    def is_invalid(self) -> bool:
        """Whether the email state is 'invalid'."""
        return self.state == "invalid"

    @property
    def is_risky(self) -> bool:
        """Whether the email state is 'risky'."""
        return self.state == "risky"

    @property
    def is_unknown(self) -> bool:
        """Whether the email state is 'unknown'."""
        return self.state == "unknown"


@dataclass(frozen=True)
class AccountInfo:
    """Account information for the authenticated user."""

    email: str
    plan: str
    credits: int
