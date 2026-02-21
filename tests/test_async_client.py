from __future__ import annotations

import httpx
import pytest
import respx

from tests.conftest import (
    API_KEY,
    BASE_URL,
    account_response,
    disposable_email_response,
    invalid_email_response,
    risky_email_response,
    suggestion_email_response,
    unknown_email_response,
    valid_email_response,
)
from truelist import (
    ApiError,
    AsyncTruelist,
    AuthenticationError,
    ConnectionError,
    RateLimitError,
    TimeoutError,
    ValidationResult,
)
from truelist._version import __version__


class TestAsyncEmailValidate:
    """Tests for async client.email.validate()."""

    @respx.mock
    async def test_valid_email(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(200, json=valid_email_response())
        )
        async with AsyncTruelist(API_KEY) as client:
            result = await client.email.validate("user@example.com")

        assert isinstance(result, ValidationResult)
        assert result.email == "user@example.com"
        assert result.domain == "example.com"
        assert result.canonical == "user"
        assert result.state == "ok"
        assert result.sub_state == "email_ok"
        assert result.verified_at == "2026-02-21T10:00:00.000Z"
        assert result.suggestion is None
        assert result.is_valid is True
        assert result.is_invalid is False
        assert result.is_risky is False
        assert result.is_unknown is False

    @respx.mock
    async def test_invalid_email(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(200, json=invalid_email_response())
        )
        async with AsyncTruelist(API_KEY) as client:
            result = await client.email.validate("bad@invalid.com")

        assert result.state == "email_invalid"
        assert result.is_invalid is True

    @respx.mock
    async def test_risky_email(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(200, json=risky_email_response())
        )
        async with AsyncTruelist(API_KEY) as client:
            result = await client.email.validate("info@company.com")

        assert result.state == "risky"
        assert result.is_risky is True
        assert result.is_role is True

    @respx.mock
    async def test_unknown_email(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(200, json=unknown_email_response())
        )
        async with AsyncTruelist(API_KEY) as client:
            result = await client.email.validate("mystery@timeout.com")

        assert result.state == "unknown"
        assert result.is_unknown is True

    @respx.mock
    async def test_disposable_email(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(200, json=disposable_email_response())
        )
        async with AsyncTruelist(API_KEY) as client:
            result = await client.email.validate("temp@mailinator.com")

        assert result.is_disposable is True

    @respx.mock
    async def test_email_with_suggestion(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(200, json=suggestion_email_response())
        )
        async with AsyncTruelist(API_KEY) as client:
            result = await client.email.validate("user@gmial.com")

        assert result.suggestion == "user@gmail.com"


class TestAsyncAccountGet:
    """Tests for async client.account.get()."""

    @respx.mock
    async def test_get_account(self) -> None:
        respx.get(f"{BASE_URL}/me").mock(
            return_value=httpx.Response(200, json=account_response())
        )
        async with AsyncTruelist(API_KEY) as client:
            account = await client.account.get()

        assert account.email == "team@company.com"
        assert account.name == "Team Lead"
        assert account.uuid == "a3828d19-1234-5678-9abc-def012345678"
        assert account.time_zone == "America/New_York"
        assert account.is_admin_role is True
        assert account.payment_plan == "pro"


class TestAsyncErrorHandling:
    """Tests for async HTTP error handling."""

    @respx.mock
    async def test_authentication_error(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(401, text="Unauthorized")
        )
        async with AsyncTruelist(API_KEY, max_retries=0) as client:
            with pytest.raises(AuthenticationError) as exc_info:
                await client.email.validate("user@example.com")

        assert exc_info.value.status_code == 401

    @respx.mock
    async def test_rate_limit_error(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(
                429,
                text="Too Many Requests",
                headers={"Retry-After": "3"},
            )
        )
        async with AsyncTruelist(API_KEY, max_retries=0) as client:
            with pytest.raises(RateLimitError) as exc_info:
                await client.email.validate("user@example.com")

        assert exc_info.value.retry_after == 3.0

    @respx.mock
    async def test_server_error(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        async with AsyncTruelist(API_KEY, max_retries=0) as client:
            with pytest.raises(ApiError) as exc_info:
                await client.email.validate("user@example.com")

        assert exc_info.value.status_code == 500

    @respx.mock
    async def test_timeout_error(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            side_effect=httpx.ReadTimeout("Read timed out")
        )
        async with AsyncTruelist(API_KEY, max_retries=0) as client:
            with pytest.raises(TimeoutError):
                await client.email.validate("user@example.com")

    @respx.mock
    async def test_connection_error(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        async with AsyncTruelist(API_KEY, max_retries=0) as client:
            with pytest.raises(ConnectionError):
                await client.email.validate("user@example.com")


class TestAsyncRetries:
    """Tests for async retry behavior."""

    @respx.mock
    async def test_retry_on_500_then_success(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/verify_inline")
        route.side_effect = [
            httpx.Response(500, text="Error"),
            httpx.Response(200, json=valid_email_response()),
        ]
        async with AsyncTruelist(API_KEY, max_retries=1) as client:
            result = await client.email.validate("user@example.com")

        assert result.is_valid is True
        assert route.call_count == 2

    @respx.mock
    async def test_retry_on_429_then_success(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/verify_inline")
        route.side_effect = [
            httpx.Response(429, text="Rate Limited", headers={"Retry-After": "0"}),
            httpx.Response(200, json=valid_email_response()),
        ]
        async with AsyncTruelist(API_KEY, max_retries=1) as client:
            result = await client.email.validate("user@example.com")

        assert result.is_valid is True
        assert route.call_count == 2

    @respx.mock
    async def test_retry_exhausted_raises(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/verify_inline")
        route.side_effect = [
            httpx.Response(502, text="Bad Gateway"),
            httpx.Response(502, text="Bad Gateway"),
            httpx.Response(502, text="Bad Gateway"),
        ]
        async with AsyncTruelist(API_KEY, max_retries=2) as client:
            with pytest.raises(ApiError) as exc_info:
                await client.email.validate("user@example.com")

        assert exc_info.value.status_code == 502
        assert route.call_count == 3

    @respx.mock
    async def test_no_retry_on_auth_error(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/verify_inline")
        route.mock(return_value=httpx.Response(401, text="Unauthorized"))
        async with AsyncTruelist(API_KEY, max_retries=2) as client:
            with pytest.raises(AuthenticationError):
                await client.email.validate("user@example.com")

        assert route.call_count == 1

    @respx.mock
    async def test_retry_on_connection_error_then_success(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/verify_inline")
        route.side_effect = [
            httpx.ConnectError("Connection refused"),
            httpx.Response(200, json=valid_email_response()),
        ]
        async with AsyncTruelist(API_KEY, max_retries=1) as client:
            result = await client.email.validate("user@example.com")

        assert result.is_valid is True
        assert route.call_count == 2


class TestAsyncClientConfiguration:
    """Tests for async client configuration."""

    @respx.mock
    async def test_user_agent_header(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(200, json=valid_email_response())
        )
        async with AsyncTruelist(API_KEY) as client:
            await client.email.validate("user@example.com")

        request = route.calls[0].request
        assert request.headers["User-Agent"] == f"truelist-python/{__version__}"

    @respx.mock
    async def test_authorization_header(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(200, json=valid_email_response())
        )
        async with AsyncTruelist(API_KEY) as client:
            await client.email.validate("user@example.com")

        request = route.calls[0].request
        assert request.headers["Authorization"] == f"Bearer {API_KEY}"

    async def test_async_context_manager(self) -> None:
        async with AsyncTruelist(API_KEY) as client:
            assert client is not None
