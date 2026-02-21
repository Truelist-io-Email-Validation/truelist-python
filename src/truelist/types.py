from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationResult:
    """Result of an email validation request."""

    email: str
    domain: str
    canonical: str | None
    mx_record: str | None
    first_name: str | None
    last_name: str | None
    state: str
    sub_state: str
    verified_at: str | None
    suggestion: str | None

    @property
    def is_valid(self) -> bool:
        """Whether the email state is 'ok'."""
        return self.state == "ok"

    @property
    def is_invalid(self) -> bool:
        """Whether the email state is 'email_invalid'."""
        return self.state == "email_invalid"

    @property
    def is_risky(self) -> bool:
        """Whether the email state is 'risky'."""
        return self.state == "risky"

    @property
    def is_unknown(self) -> bool:
        """Whether the email state is 'unknown'."""
        return self.state == "unknown"

    @property
    def is_disposable(self) -> bool:
        """Whether the email sub_state is 'is_disposable'."""
        return self.sub_state == "is_disposable"

    @property
    def is_role(self) -> bool:
        """Whether the email sub_state is 'is_role'."""
        return self.sub_state == "is_role"


@dataclass(frozen=True)
class AccountInfo:
    """Account information for the authenticated user."""

    email: str
    name: str
    uuid: str
    time_zone: str | None
    is_admin_role: bool
    payment_plan: str
