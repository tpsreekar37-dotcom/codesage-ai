import pytest
from unittest.mock import patch
import uuid
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_analysis_missing_repo(client: AsyncClient):
    # Register and Login
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "analysis_user@domain.com",
            "password": "analysispassword",
            "full_name": "Reviewer"
        }
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "analysis_user@domain.com",
            "password": "analysispassword"
        }
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to analyze a non-existing repository UUID
    random_uuid = str(uuid.uuid4())
    response = await client.post(
        "/api/v1/analyses",
        headers=headers,
        json={"repository_id": random_uuid}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found."
