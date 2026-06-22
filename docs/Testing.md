# Testing Suite Documentation

The application implements high-coverage unit and integration tests for backend APIs, auth handlers, and file operations.

## Test Structure
Tests are located inside `backend/tests/` and use `pytest` and `pytest-asyncio`.

- `conftest.py`: Bootstraps an in-memory SQLite database instance (`sqlite+aiosqlite:///:memory:`). This enables database tests to run instantly without requiring a live PostgreSQL service.
- `test_auth.py`: Tests user registration flow, login validations, and `/me` profiles.
- `test_repositories.py`: Tests secure folder uploading and Git cloning endpoints using `unittest.mock`.
- `test_analyses.py`: Verifies validator constraints when trying to query/create non-existing analyses.
- `test_ai_service.py`: Unit tests checking that the scanner ignores files (like `node_modules/` or `.git/`) and the mock report generator falls back correctly.

---

## Executing Tests

1. Activate your virtual environment inside `backend/`:
   ```bash
   cd backend
   .\venv\Scripts\Activate.ps1
   ```
2. Run the test suite:
   ```bash
   pytest
   ```
3. To view test coverage metrics:
   ```bash
   pytest --cov=app tests/
   ```
