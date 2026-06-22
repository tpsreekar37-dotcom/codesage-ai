# Database Schema

The application database is PostgreSQL 16. The schema is normalized, leveraging UUID primary keys and indexes.

## Entity Relationship Diagrams

```
  ┌──────────────┐          ┌────────────────┐
  │    users     │◄─────────┤    sessions    │
  │ (User Model) │          │ (UserSession)  │
  └──────┬───────┘          └────────────────┘
         │
         │ 1
         │
         │ N
  ┌──────▼───────┐          ┌────────────────┐
  │ repositories │◄─────────┤   audit_logs   │
  │ (Repository) │          │  (AuditLog)    │
  └──────┬───────┘          └────────────────┘
         │
         │ 1
         │
         │ N
  ┌──────▼───────┐
  │   analyses   │
  │  (Analysis)  │
  └──────┬───────┘
         │
         │ 1 (One-To-One)
         │
         ▼
  ┌──────────────┐
  │   reports    │
  │   (Report)   │
  └──────────────┘
```

## Tables & Fields

### `users`
- `id` (UUID, PK, Index)
- `email` (VARCHAR(255), Unique, Index, Not Null)
- `hashed_password` (VARCHAR(255), Not Null)
- `full_name` (VARCHAR(255))
- `role` (VARCHAR(50), default 'user', Not Null)
- `is_active` (BOOLEAN, default True, Not Null)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### `repositories`
- `id` (UUID, PK, Index)
- `name` (VARCHAR(255), Not Null)
- `type` (VARCHAR(50), Not Null) # "zip", "github"
- `github_url` (VARCHAR(1024))
- `file_path` (VARCHAR(1024))
- `status` (VARCHAR(50), default 'active', Not Null)
- `owner_id` (UUID, FK -> users.id, Index, Cascade)
- `created_at` (TIMESTAMP)

### `analyses`
- `id` (UUID, PK, Index)
- `repository_id` (UUID, FK -> repositories.id, Index, Cascade)
- `status` (VARCHAR(50), default 'pending', Not Null) # "pending", "processing", "completed", "failed"
- `error_message` (VARCHAR(2048))
- `created_at` (TIMESTAMP)
- `completed_at` (TIMESTAMP)

### `reports`
- `id` (UUID, PK, Index)
- `analysis_id` (UUID, FK -> analyses.id, Unique, Index, Cascade)
- `score_quality` (INT)
- `score_security` (INT)
- `score_performance` (INT)
- `score_maintainability` (INT)
- `findings` (JSON)
- `markdown_content` (TEXT)
- `created_at` (TIMESTAMP)

### `sessions`
- `id` (UUID, PK, Index)
- `user_id` (UUID, FK -> users.id, Index, Cascade)
- `refresh_token` (VARCHAR(512), Unique, Index, Not Null)
- `is_revoked` (BOOLEAN, default False, Not Null)
- `ip_address` (VARCHAR(45))
- `user_agent` (VARCHAR(512))
- `created_at` (TIMESTAMP)
- `expires_at` (TIMESTAMP)

### `audit_logs`
- `id` (UUID, PK, Index)
- `user_id` (UUID, FK -> users.id, Nullable, Index, Set Null)
- `action` (VARCHAR(100), Not Null)
- `details` (JSON, Not Null)
- `ip_address` (VARCHAR(45))
- `created_at` (TIMESTAMP)
