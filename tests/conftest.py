from __future__ import annotations

from typing import Any

import pytest

API_KEY = "test-api-key-12345"
BASE_URL = "https://api.truelist.io"


def valid_email_response() -> dict[str, Any]:
    return {
        "email": "user@example.com",
        "state": "valid",
        "sub_state": "ok",
        "free_email": True,
        "role": False,
        "disposable": False,
        "suggestion": None,
    }


def invalid_email_response() -> dict[str, Any]:
    return {
        "email": "bad@invalid.com",
        "state": "invalid",
        "sub_state": "failed_no_mailbox",
        "free_email": False,
        "role": False,
        "disposable": False,
        "suggestion": None,
    }


def risky_email_response() -> dict[str, Any]:
    return {
        "email": "info@company.com",
        "state": "risky",
        "sub_state": "accept_all",
        "free_email": False,
        "role": True,
        "disposable": False,
        "suggestion": None,
    }


def unknown_email_response() -> dict[str, Any]:
    return {
        "email": "mystery@timeout.com",
        "state": "unknown",
        "sub_state": "failed_greylisted",
        "free_email": False,
        "role": False,
        "disposable": False,
        "suggestion": None,
    }


def disposable_email_response() -> dict[str, Any]:
    return {
        "email": "temp@mailinator.com",
        "state": "invalid",
        "sub_state": "disposable_address",
        "free_email": True,
        "role": False,
        "disposable": True,
        "suggestion": None,
    }


def suggestion_email_response() -> dict[str, Any]:
    return {
        "email": "user@gmial.com",
        "state": "invalid",
        "sub_state": "failed_no_mailbox",
        "free_email": False,
        "role": False,
        "disposable": False,
        "suggestion": "user@gmail.com",
    }


def account_response() -> dict[str, Any]:
    return {
        "email": "owner@truelist.io",
        "plan": "pro",
        "credits": 9500,
    }


@pytest.fixture()
def api_key() -> str:
    return API_KEY
