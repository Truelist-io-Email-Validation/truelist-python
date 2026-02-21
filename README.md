# Truelist Python SDK

Official Python SDK for the [Truelist.io](https://truelist.io) email validation API. Validate email addresses in real-time with a simple, type-safe interface.

- Sync and async clients
- Automatic retries with exponential backoff
- Full type annotations (mypy strict compatible)
- Minimal dependencies (just `httpx`)
- Python 3.9+

## Installation

```bash
pip install truelist
```

## Quick Start

```python
from truelist import Truelist

client = Truelist("your-api-key")

result = client.email.validate("user@example.com")
print(result.state)       # "ok"
print(result.sub_state)   # "email_ok"
print(result.domain)      # "example.com"
print(result.is_valid)    # True
```

## Async Usage

```python
from truelist import AsyncTruelist

client = AsyncTruelist("your-api-key")

result = await client.email.validate("user@example.com")
print(result.is_valid)

await client.close()
```

Or use an async context manager:

```python
async with AsyncTruelist("your-api-key") as client:
    result = await client.email.validate("user@example.com")
```

## Error Handling

```python
from truelist import Truelist, AuthenticationError, RateLimitError, ApiError

client = Truelist("your-api-key")

try:
    result = client.email.validate("user@example.com")
except AuthenticationError:
    # Invalid or missing API key (HTTP 401/403)
    print("Check your API key")
except RateLimitError as e:
    # Too many requests (HTTP 429)
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except ApiError as e:
    # Other API errors
    print(f"API error {e.status_code}: {e.message}")
```

All errors inherit from `TruelistError`, so you can catch that as a catch-all:

```python
from truelist import TruelistError

try:
    result = client.email.validate("user@example.com")
except TruelistError as e:
    print(f"Something went wrong: {e.message}")
```

## Configuration

```python
client = Truelist(
    "your-api-key",
    base_url="https://api.truelist.io",  # default
    timeout=30.0,                         # seconds, default
    max_retries=2,                        # default
)
```

## Context Manager

Both sync and async clients support context managers for automatic cleanup:

```python
# Sync
with Truelist("your-api-key") as client:
    result = client.email.validate("user@example.com")

# Async
async with AsyncTruelist("your-api-key") as client:
    result = await client.email.validate("user@example.com")
```

## Retries

The SDK automatically retries failed requests with exponential backoff:

- **Retried**: HTTP 429 (rate limit), 500, 502, 503, 504, connection errors, timeouts
- **Not retried**: HTTP 401, 403, 422, and other client errors
- **Backoff**: Starts at 0.5s, doubles each attempt, capped at 8s
- **429 responses**: Uses the `Retry-After` header when provided

Set `max_retries=0` to disable retries.

## API Methods

### Email Validation

```python
result = client.email.validate("user@example.com")
```

### Account Info

```python
account = client.account.get()
print(account.email)         # "you@company.com"
print(account.name)          # "Your Name"
print(account.payment_plan)  # "pro"
```

## Types Reference

### `ValidationResult`

| Field | Type | Description |
|-------|------|-------------|
| `email` | `str` | The email address that was validated |
| `domain` | `str` | The domain of the email address |
| `canonical` | `str \| None` | The canonical (local) part of the email |
| `mx_record` | `str \| None` | The MX record for the domain |
| `first_name` | `str \| None` | First name associated with the email, if available |
| `last_name` | `str \| None` | Last name associated with the email, if available |
| `state` | `str` | One of: `ok`, `email_invalid`, `risky`, `unknown`, `accept_all` |
| `sub_state` | `str` | Detailed reason (see below) |
| `verified_at` | `str \| None` | Timestamp of when the verification was performed |
| `suggestion` | `str \| None` | Suggested correction, if any |

Convenience properties: `is_valid`, `is_invalid`, `is_risky`, `is_unknown`, `is_disposable`, `is_role`

#### Sub-states

| Sub-state | Description |
|-----------|-------------|
| `email_ok` | Email is valid |
| `is_disposable` | Disposable email provider |
| `is_role` | Role-based address (info@, admin@, etc.) |
| `unknown_error` | Could not determine status |
| `failed_smtp_check` | SMTP check failed |

### `AccountInfo`

| Field | Type | Description |
|-------|------|-------------|
| `email` | `str` | Account email address |
| `name` | `str` | Account holder name |
| `uuid` | `str` | Account UUID |
| `time_zone` | `str \| None` | Account time zone |
| `is_admin_role` | `bool` | Whether the user has admin role |
| `payment_plan` | `str` | Current payment plan |

### Exceptions

| Exception | Description |
|-----------|-------------|
| `TruelistError` | Base exception for all SDK errors |
| `AuthenticationError` | Invalid or missing API key (401/403) |
| `RateLimitError` | Rate limit exceeded (429) |
| `ApiError` | Other API errors (has `status_code` and `body`) |
| `ConnectionError` | Failed to connect to API |
| `TimeoutError` | Request timed out |

## License

MIT
