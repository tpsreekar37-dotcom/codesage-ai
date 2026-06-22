import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "testuser@domain.com",
            "password": "testpassword",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "testuser@domain.com"
    assert "id" in data
    assert "role" in data

@pytest.mark.asyncio
async def test_login_user(client: AsyncClient):
    # Register user first
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "testuser2@domain.com",
            "password": "testpassword2",
            "full_name": "Test User 2"
        }
    )

    # Login
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "testuser2@domain.com",
            "password": "testpassword2"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_get_me(client: AsyncClient):
    # Register and Login
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "testuser3@domain.com",
            "password": "testpassword3",
            "full_name": "Test User 3"
        }
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "testuser3@domain.com",
            "password": "testpassword3"
        }
    )
    token = login_res.json()["access_token"]

    # Query me endpoint with authorization header
    headers = {"Authorization": f"Bearer {token}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "testuser3@domain.com"
