# System Architecture

The AI Code Review Platform is built following a clean, layered architecture pattern, designed to isolate responsibilities, maximize testability, and ensure scalability.

## Architecture Layers

```
                               ┌───────────────┐
                               │  React Client │
                               └───────┬───────┘
                                       │ REST HTTP / JSON
                                       ▼
                               ┌───────────────┐
                               │  FastAPI API  │ (api/v1/)
                               └───────┬───────┘
                                       │
                                       ▼
 ┌───────────────────┐         ┌───────────────┐
 │   Redis Cache     │◄────────►  Services     ├────────┐
 │ (dashboard, rate) │         │ (Business)    │        │
 └───────────────────┘         └───────┬───────┘        │ Background Task
                                       │                ▼
                                       ▼         ┌───────────────┐
                               ┌───────────────┐ │ Google Gemini │
                               │ Repositories  │ └───────────────┘
                               └───────┬───────┘
                                       │ SQLAlchemy (Async)
                                       ▼
                               ┌───────────────┐
                               │  PostgreSQL   │
                               └───────────────┘
```

1. **API Router Layer (`api/v1/`)**: Handles incoming HTTP requests, performs input validations using Pydantic, checks authentication, and returns proper status codes/JSON responses.
2. **Business Services Layer (`services/`)**: Contains implementation details of domain operations:
   - `RepoManagerService`: Handles disk management, ZIP safe-extraction, and secure Git cloning.
   - `AIEngineService`: Directory codebase scanner and structured prompt generator interfacing with Google Gemini.
3. **Repository Data Access Layer (`repositories/`)**: Abstract database operations utilizing SQLAlchemy async sessions. Enforces strict types and isolates query construction.
4. **Models Layer (`models/`)**: Declarative SQLAlchemy models representing SQL tables.

## Caching Strategy
- **Dashboard Stats**: Calculated via database grouping aggregates. Buffered in Redis using client key namespaces (e.g. `user:dashboard_stats:{uuid}`) with a TTL of 60 seconds to mitigate database load.
- **Rate Limiting**: Built into a custom ASGI middleware. Increments request counts in Redis in sliding 60-second windows. Fails open gracefully to prevent system lockouts if Redis goes down.

## Background Execution Flow
To keep HTTP operations fast:
1. When a user requests to run an AI review, the `/analyses` endpoint instantiates an `Analysis` DB record set to `pending`.
2. The FastAPI `BackgroundTasks` runner spawns an asynchronous review job.
3. The HTTP response returns the pending analysis metadata immediately, allowing the client to return to the dashboard.
4. The background thread changes the status to `processing`, reads code contents, calls Gemini, creates a `Report` record, and marks the status as `completed`.
5. The frontend polls the status of the analysis and swaps into the completed visualization layout when finished.
