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
print(result.state)       # "valid"
print(result.sub_state)   # "ok"
print(result.free_email)  # True
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
# Server-side validation
result = client.email.validate("user@example.com")

# Form/frontend validation (different rate limits)
result = client.email.form_validate("user@example.com")
```

### Account Info

```python
account = client.account.get()
print(account.email)    # "you@company.com"
print(account.plan)     # "pro"
print(account.credits)  # 9500
```

## Types Reference

### `ValidationResult`

| Field | Type | Description |
|-------|------|-------------|
| `email` | `str` | The email address that was validated |
| `state` | `str` | One of: `valid`, `invalid`, `risky`, `unknown` |
| `sub_state` | `str` | Detailed reason (see below) |
| `free_email` | `bool` | Whether the email is from a free provider |
| `role` | `bool` | Whether the email is a role address (e.g., info@) |
| `disposable` | `bool` | Whether the email is from a disposable provider |
| `suggestion` | `str \| None` | Suggested correction, if any |

Convenience properties: `is_valid`, `is_invalid`, `is_risky`, `is_unknown`

#### Sub-states

| Sub-state | Description |
|-----------|-------------|
| `ok` | Email is valid |
| `accept_all` | Domain accepts all emails (risky) |
| `disposable_address` | Disposable email provider |
| `role_address` | Role-based address (info@, admin@, etc.) |
| `failed_mx_check` | Domain has no MX records |
| `failed_spam_trap` | Known spam trap |
| `failed_no_mailbox` | Mailbox does not exist |
| `failed_greylisted` | Server temporarily rejected (greylisting) |
| `failed_syntax_check` | Email syntax is invalid |
| `unknown` | Could not determine status |

### `AccountInfo`

| Field | Type | Description |
|-------|------|-------------|
| `email` | `str` | Account email address |
| `plan` | `str` | Current plan name |
| `credits` | `int` | Remaining validation credits |

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
