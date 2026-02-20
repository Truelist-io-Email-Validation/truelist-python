from __future__ import annotations

import time
from typing import Any

import httpx

from truelist._version import __version__
from truelist.errors import (
    ApiError,
    AuthenticationError,
    ConnectionError,
    RateLimitError,
    TimeoutError,
    TruelistError,
)

DEFAULT_BASE_URL = "https://api.truelist.io"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2

_RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
_INITIAL_BACKOFF = 0.5
_BACKOFF_MULTIPLIER = 2.0
_MAX_BACKOFF = 8.0


def build_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": f"truelist-python/{__version__}",
    }


def build_client_kwargs(
    *,
    api_key: str,
    base_url: str,
    timeout: float,
) -> dict[str, Any]:
    return {
        "base_url": base_url,
        "headers": build_headers(api_key),
        "timeout": httpx.Timeout(timeout),
    }


def _parse_retry_after(response: httpx.Response) -> float | None:
    retry_after = response.headers.get("Retry-After")
    if retry_after is None:
        return None
    try:
        return float(retry_after)
    except (ValueError, TypeError):
        return None


def _compute_backoff(attempt: int) -> float:
    delay = _INITIAL_BACKOFF * (_BACKOFF_MULTIPLIER**attempt)
    return min(delay, _MAX_BACKOFF)


def _raise_for_status(response: httpx.Response) -> None:
    if response.status_code >= 400:
        body = response.text
        if response.status_code in (401, 403):
            raise AuthenticationError(
                message=f"Authentication failed (HTTP {response.status_code})",
                status_code=response.status_code,
                body=body,
            )
        if response.status_code == 429:
            retry_after = _parse_retry_after(response)
            raise RateLimitError(
                message="Rate limit exceeded (HTTP 429)",
                status_code=429,
                body=body,
                retry_after=retry_after,
            )
        raise ApiError(
            message=f"API error (HTTP {response.status_code})",
            status_code=response.status_code,
            body=body,
        )


def should_retry(response: httpx.Response) -> bool:
    return response.status_code in _RETRY_STATUS_CODES


def sync_request(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    max_retries: int,
    json: dict[str, Any] | None = None,
) -> httpx.Response:
    last_exc: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            response = client.request(method, url, json=json)
        except httpx.ConnectError as exc:
            last_exc = exc
            if attempt < max_retries:
                time.sleep(_compute_backoff(attempt))
                continue
            raise ConnectionError(str(exc)) from exc
        except httpx.TimeoutException as exc:
            last_exc = exc
            if attempt < max_retries:
                time.sleep(_compute_backoff(attempt))
                continue
            raise TimeoutError(str(exc)) from exc

        if should_retry(response) and attempt < max_retries:
            if response.status_code == 429:
                retry_after = _parse_retry_after(response)
                delay = retry_after if retry_after is not None else _compute_backoff(attempt)
            else:
                delay = _compute_backoff(attempt)
            time.sleep(delay)
            continue

        _raise_for_status(response)
        return response

    if last_exc is not None:  # pragma: no cover
        raise ConnectionError(str(last_exc)) from last_exc
    raise TruelistError("Request failed after retries")  # pragma: no cover


async def async_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    max_retries: int,
    json: dict[str, Any] | None = None,
) -> httpx.Response:
    import asyncio

    last_exc: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            response = await client.request(method, url, json=json)
        except httpx.ConnectError as exc:
            last_exc = exc
            if attempt < max_retries:
                await asyncio.sleep(_compute_backoff(attempt))
                continue
            raise ConnectionError(str(exc)) from exc
        except httpx.TimeoutException as exc:
            last_exc = exc
            if attempt < max_retries:
                await asyncio.sleep(_compute_backoff(attempt))
                continue
            raise TimeoutError(str(exc)) from exc

        if should_retry(response) and attempt < max_retries:
            if response.status_code == 429:
                retry_after = _parse_retry_after(response)
                delay = retry_after if retry_after is not None else _compute_backoff(attempt)
            else:
                delay = _compute_backoff(attempt)
            await asyncio.sleep(delay)
            continue

        _raise_for_status(response)
        return response

    if last_exc is not None:  # pragma: no cover
        raise ConnectionError(str(last_exc)) from last_exc
    raise TruelistError("Request failed after retries")  # pragma: no cover
