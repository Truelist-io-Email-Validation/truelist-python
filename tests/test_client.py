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
    AuthenticationError,
    ConnectionError,
    RateLimitError,
    TimeoutError,
    Truelist,
    ValidationResult,
)
from truelist._version import __version__


class TestEmailValidate:
    """Tests for client.email.validate()."""

    @respx.mock
    def test_valid_email(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(200, json=valid_email_response())
        )
        with Truelist(API_KEY) as client:
            result = client.email.validate("user@example.com")

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
    def test_invalid_email(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(200, json=invalid_email_response())
        )
        with Truelist(API_KEY) as client:
            result = client.email.validate("bad@invalid.com")

        assert result.state == "email_invalid"
        assert result.sub_state == "unknown_error"
        assert result.is_valid is False
        assert result.is_invalid is True

    @respx.mock
    def test_risky_email(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(200, json=risky_email_response())
        )
        with Truelist(API_KEY) as client:
            result = client.email.validate("info@company.com")

        assert result.state == "risky"
        assert result.sub_state == "is_role"
        assert result.is_role is True
        assert result.is_risky is True

    @respx.mock
    def test_unknown_email(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(200, json=unknown_email_response())
        )
        with Truelist(API_KEY) as client:
            result = client.email.validate("mystery@timeout.com")

        assert result.state == "unknown"
        assert result.sub_state == "failed_smtp_check"
        assert result.is_unknown is True

    @respx.mock
    def test_disposable_email(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(200, json=disposable_email_response())
        )
        with Truelist(API_KEY) as client:
            result = client.email.validate("temp@mailinator.com")

        assert result.is_disposable is True
        assert result.sub_state == "is_disposable"

    @respx.mock
    def test_email_with_suggestion(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(200, json=suggestion_email_response())
        )
        with Truelist(API_KEY) as client:
            result = client.email.validate("user@gmial.com")

        assert result.suggestion == "user@gmail.com"

    @respx.mock
    def test_validation_result_is_frozen(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(200, json=valid_email_response())
        )
        with Truelist(API_KEY) as client:
            result = client.email.validate("user@example.com")

        with pytest.raises(AttributeError):
            result.state = "email_invalid"  # type: ignore[misc]


class TestAccountGet:
    """Tests for client.account.get()."""

    @respx.mock
    def test_get_account(self) -> None:
        respx.get(f"{BASE_URL}/me").mock(
            return_value=httpx.Response(200, json=account_response())
        )
        with Truelist(API_KEY) as client:
            account = client.account.get()

        assert account.email == "team@company.com"
        assert account.name == "Team Lead"
        assert account.uuid == "a3828d19-1234-5678-9abc-def012345678"
        assert account.time_zone == "America/New_York"
        assert account.is_admin_role is True
        assert account.payment_plan == "pro"


class TestErrorHandling:
    """Tests for HTTP error handling."""

    @respx.mock
    def test_authentication_error_401(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(401, text="Unauthorized")
        )
        with (
            Truelist(API_KEY, max_retries=0) as client,
            pytest.raises(AuthenticationError) as exc_info,
        ):
            client.email.validate("user@example.com")

        assert exc_info.value.status_code == 401
        assert exc_info.value.body == "Unauthorized"

    @respx.mock
    def test_authentication_error_403(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(403, text="Forbidden")
        )
        with (
            Truelist(API_KEY, max_retries=0) as client,
            pytest.raises(AuthenticationError) as exc_info,
        ):
            client.email.validate("user@example.com")

        assert exc_info.value.status_code == 403

    @respx.mock
    def test_rate_limit_error(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(
                429,
                text="Too Many Requests",
                headers={"Retry-After": "5"},
            )
        )
        with Truelist(API_KEY, max_retries=0) as client, pytest.raises(RateLimitError) as exc_info:
            client.email.validate("user@example.com")

        assert exc_info.value.status_code == 429
        assert exc_info.value.retry_after == 5.0

    @respx.mock
    def test_server_error_500(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        with Truelist(API_KEY, max_retries=0) as client, pytest.raises(ApiError) as exc_info:
            client.email.validate("user@example.com")

        assert exc_info.value.status_code == 500

    @respx.mock
    def test_api_error_422(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(422, text="Unprocessable Entity")
        )
        with Truelist(API_KEY, max_retries=0) as client, pytest.raises(ApiError) as exc_info:
            client.email.validate("user@example.com")

        assert exc_info.value.status_code == 422

    @respx.mock
    def test_timeout_error(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            side_effect=httpx.ReadTimeout("Read timed out")
        )
        with Truelist(API_KEY, max_retries=0) as client, pytest.raises(TimeoutError):
            client.email.validate("user@example.com")

    @respx.mock
    def test_connection_error(self) -> None:
        respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        with Truelist(API_KEY, max_retries=0) as client, pytest.raises(ConnectionError):
            client.email.validate("user@example.com")


class TestRetries:
    """Tests for retry behavior."""

    @respx.mock
    def test_retry_on_500_then_success(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/verify_inline")
        route.side_effect = [
            httpx.Response(500, text="Internal Server Error"),
            httpx.Response(200, json=valid_email_response()),
        ]
        with Truelist(API_KEY, max_retries=1) as client:
            result = client.email.validate("user@example.com")

        assert result.is_valid is True
        assert route.call_count == 2

    @respx.mock
    def test_retry_on_429_then_success(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/verify_inline")
        route.side_effect = [
            httpx.Response(429, text="Rate Limited", headers={"Retry-After": "0"}),
            httpx.Response(200, json=valid_email_response()),
        ]
        with Truelist(API_KEY, max_retries=1) as client:
            result = client.email.validate("user@example.com")

        assert result.is_valid is True
        assert route.call_count == 2

    @respx.mock
    def test_retry_exhausted_raises(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/verify_inline")
        route.side_effect = [
            httpx.Response(500, text="Error"),
            httpx.Response(500, text="Error"),
            httpx.Response(500, text="Error"),
        ]
        with Truelist(API_KEY, max_retries=2) as client, pytest.raises(ApiError) as exc_info:
            client.email.validate("user@example.com")

        assert exc_info.value.status_code == 500
        assert route.call_count == 3

    @respx.mock
    def test_retry_on_connection_error_then_success(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/verify_inline")
        route.side_effect = [
            httpx.ConnectError("Connection refused"),
            httpx.Response(200, json=valid_email_response()),
        ]
        with Truelist(API_KEY, max_retries=1) as client:
            result = client.email.validate("user@example.com")

        assert result.is_valid is True
        assert route.call_count == 2

    @respx.mock
    def test_retry_on_timeout_then_success(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/verify_inline")
        route.side_effect = [
            httpx.ReadTimeout("Timeout"),
            httpx.Response(200, json=valid_email_response()),
        ]
        with Truelist(API_KEY, max_retries=1) as client:
            result = client.email.validate("user@example.com")

        assert result.is_valid is True
        assert route.call_count == 2

    @respx.mock
    def test_no_retry_on_401(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/verify_inline")
        route.mock(return_value=httpx.Response(401, text="Unauthorized"))
        with Truelist(API_KEY, max_retries=2) as client, pytest.raises(AuthenticationError):
            client.email.validate("user@example.com")

        assert route.call_count == 1

    @respx.mock
    def test_no_retry_on_422(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/verify_inline")
        route.mock(return_value=httpx.Response(422, text="Bad Request"))
        with Truelist(API_KEY, max_retries=2) as client, pytest.raises(ApiError):
            client.email.validate("user@example.com")

        assert route.call_count == 1


class TestClientConfiguration:
    """Tests for client construction and configuration."""

    @respx.mock
    def test_custom_base_url(self) -> None:
        custom_url = "https://custom.api.truelist.io"
        respx.post(f"{custom_url}/api/v1/verify_inline").mock(
            return_value=httpx.Response(200, json=valid_email_response())
        )
        with Truelist(API_KEY, base_url=custom_url) as client:
            result = client.email.validate("user@example.com")

        assert result.is_valid is True

    @respx.mock
    def test_user_agent_header(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(200, json=valid_email_response())
        )
        with Truelist(API_KEY) as client:
            client.email.validate("user@example.com")

        request = route.calls[0].request
        assert request.headers["User-Agent"] == f"truelist-python/{__version__}"

    @respx.mock
    def test_authorization_header(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(200, json=valid_email_response())
        )
        with Truelist(API_KEY) as client:
            client.email.validate("user@example.com")

        request = route.calls[0].request
        assert request.headers["Authorization"] == f"Bearer {API_KEY}"

    @respx.mock
    def test_email_sent_as_query_param(self) -> None:
        route = respx.post(f"{BASE_URL}/api/v1/verify_inline").mock(
            return_value=httpx.Response(200, json=valid_email_response())
        )
        with Truelist(API_KEY) as client:
            client.email.validate("user@example.com")

        request = route.calls[0].request
        assert "email=user%40example.com" in str(request.url)

    def test_context_manager(self) -> None:
        with Truelist(API_KEY) as client:
            assert client is not None
