# Local Setup Instructions

This guide provides steps for running the AI Code Review Platform on your local Windows system.

## Prerequisites
- **Python 3.12** or higher
- **Node.js 20** or higher
- **Git** CLI installed
- **PostgreSQL** & **Redis** servers running locally (or via Docker)

---

## 1. Setup Environment Configuration
Copy the template `.env.example` in the root folder to `.env`:
```bash
cp .env.example .env
```
Open `.env` and fill in:
- `GEMINI_API_KEY`: Your Google Gemini API Key.
- Adjust `DATABASE_URL` and `REDIS_URL` if not running inside Docker Compose.

---

## 2. Backend Setup
1. Open a terminal and navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Create and activate a python virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate.ps1   # On PowerShell
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run Alembic migrations:
   ```bash
   alembic upgrade head
   ```
5. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

---

## 3. Frontend Setup
1. Open another terminal and navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install package dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   Open [http://localhost:5173](http://localhost:5173) in your web browser.
