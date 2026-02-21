from __future__ import annotations

from typing import Any

import pytest

API_KEY = "test-api-key-12345"
BASE_URL = "https://api.truelist.io"


def valid_email_response() -> dict[str, Any]:
    return {
        "emails": [
            {
                "address": "user@example.com",
                "domain": "example.com",
                "canonical": "user",
                "mx_record": None,
                "first_name": None,
                "last_name": None,
                "email_state": "ok",
                "email_sub_state": "email_ok",
                "verified_at": "2026-02-21T10:00:00.000Z",
                "did_you_mean": None,
            }
        ]
    }


def invalid_email_response() -> dict[str, Any]:
    return {
        "emails": [
            {
                "address": "bad@invalid.com",
                "domain": "invalid.com",
                "canonical": "bad",
                "mx_record": None,
                "first_name": None,
                "last_name": None,
                "email_state": "email_invalid",
                "email_sub_state": "unknown_error",
                "verified_at": "2026-02-21T10:00:00.000Z",
                "did_you_mean": None,
            }
        ]
    }


def risky_email_response() -> dict[str, Any]:
    return {
        "emails": [
            {
                "address": "info@company.com",
                "domain": "company.com",
                "canonical": "info",
                "mx_record": "mx.company.com",
                "first_name": None,
                "last_name": None,
                "email_state": "risky",
                "email_sub_state": "is_role",
                "verified_at": "2026-02-21T10:00:00.000Z",
                "did_you_mean": None,
            }
        ]
    }


def unknown_email_response() -> dict[str, Any]:
    return {
        "emails": [
            {
                "address": "mystery@timeout.com",
                "domain": "timeout.com",
                "canonical": "mystery",
                "mx_record": None,
                "first_name": None,
                "last_name": None,
                "email_state": "unknown",
                "email_sub_state": "failed_smtp_check",
                "verified_at": "2026-02-21T10:00:00.000Z",
                "did_you_mean": None,
            }
        ]
    }


def disposable_email_response() -> dict[str, Any]:
    return {
        "emails": [
            {
                "address": "temp@mailinator.com",
                "domain": "mailinator.com",
                "canonical": "temp",
                "mx_record": None,
                "first_name": None,
                "last_name": None,
                "email_state": "email_invalid",
                "email_sub_state": "is_disposable",
                "verified_at": "2026-02-21T10:00:00.000Z",
                "did_you_mean": None,
            }
        ]
    }


def suggestion_email_response() -> dict[str, Any]:
    return {
        "emails": [
            {
                "address": "user@gmial.com",
                "domain": "gmial.com",
                "canonical": "user",
                "mx_record": None,
                "first_name": None,
                "last_name": None,
                "email_state": "email_invalid",
                "email_sub_state": "unknown_error",
                "verified_at": "2026-02-21T10:00:00.000Z",
                "did_you_mean": "user@gmail.com",
            }
        ]
    }


def account_response() -> dict[str, Any]:
    return {
        "email": "team@company.com",
        "name": "Team Lead",
        "uuid": "a3828d19-1234-5678-9abc-def012345678",
        "time_zone": "America/New_York",
        "is_admin_role": True,
        "token": "test_token",
        "api_keys": [],
        "account": {
            "name": "Company Inc",
            "payment_plan": "pro",
            "users": [],
        },
    }


@pytest.fixture()
def api_key() -> str:
    return API_KEY
