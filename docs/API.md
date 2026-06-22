# REST API Documentation

The platform implements RESTful endpoints, validating requests using Pydantic, and enforcing JWT Bearer token authentication.

## Authentication (`/api/v1/auth`)

### Post Registration
- **URL**: `/register`
- **Method**: `POST`
- **Payload**:
  ```json
  {
    "email": "user@domain.com",
    "password": "strongpassword",
    "full_name": "Full Name"
  }
  ```
- **Response** (201 Created): User account details.

### Post Login
- **URL**: `/login`
- **Method**: `POST`
- **Payload** (Form-Data):
  - `username`: Email address
  - `password`: Password
- **Response** (200 OK):
  ```json
  {
    "access_token": "access_jwt_string",
    "refresh_token": "refresh_jwt_string",
    "token_type": "bearer"
  }
  ```

### Refresh Token
- **URL**: `/refresh`
- **Method**: `POST`
- **Query Params**: `refresh_token_in`
- **Response** (200 OK): New access and refresh tokens.

---

## Repositories (`/api/v1/repositories`)

### Upload ZIP
- **URL**: `/upload`
- **Method**: `POST`
- **Multipart Form-Data**:
  - `name`: Repository project name
  - `file`: File upload (.zip format)
- **Response** (201 Created): Repository metadata.

### Clone Git
- **URL**: `/clone`
- **Method**: `POST`
- **Multipart Form-Data**:
  - `name`: Repository project name
  - `git_url`: Public HTTP Git clone URL
- **Response** (201 Created): Repository metadata.

---

## Analyses & Reports (`/api/v1/analyses`, `/api/v1/reports`)

### Start Analysis
- **URL**: `/analyses`
- **Method**: `POST`
- **Payload**:
  ```json
  {
    "repository_id": "repository_uuid"
  }
  ```
- **Response** (201 Created): Pending analysis metadata.

### Get Report
- **URL**: `/reports/analysis/{analysis_id}`
- **Method**: `GET`
- **Response** (200 OK): Detailed review report containing quality scores, specific findings, and markdown document.
