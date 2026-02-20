# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-20

### Added

- Initial release
- Sync client (`Truelist`) and async client (`AsyncTruelist`)
- Email validation via `client.email.validate()`
- Form validation via `client.email.form_validate()`
- Account info via `client.account.get()`
- Automatic retries with exponential backoff on 429/5xx
- Full type annotations (mypy strict compatible)
- Context manager support for both sync and async clients
