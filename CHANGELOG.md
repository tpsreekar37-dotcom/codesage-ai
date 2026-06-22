# Changelog

All notable changes to the **AI Code Review Platform** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-19

### Added
- Modular clean architecture backend with FastAPI and asynchronous database mappings using SQLAlchemy.
- Declared models for `users`, `repositories`, `analyses`, `reports`, `sessions`, and `audit_logs`.
- Interactive frontend UI using Vite, React, and TypeScript.
- Custom dynamic Markdown-to-HTML parser rendering reports with alerts and code blocks.
- Safe local folder ZIP extraction with path traversal defense mechanisms.
- Shallow Git repository cloning functionality with timeout safeguards.
- Rate-limiting middleware using Redis token-bucket schemes (with fail-open mock fallback).
- Mock AI Code Review Report generator fallback pathway.
- Subprocess terminal prompt disabling environment config (`GIT_TERMINAL_PROMPT=0`).

### Fixed
- Authentication passlib compatibility bug on Python 3.12, replaced with native `bcrypt` cryptography handlers.
- Standard library NameError missing import (`os`) in the API analyses router.
- Testing event-loop scoping assertion errors in `pytest-asyncio` configurations.
- HTTPX client parameters updated to comply with modern `ASGITransport` integrations.
