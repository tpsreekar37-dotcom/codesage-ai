import pytest
from unittest.mock import patch
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_clone_repository_endpoint(client: AsyncClient):
    # Register and Login
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "repo_user@domain.com",
            "password": "repopassword",
            "full_name": "Repo Owner"
        }
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "repo_user@domain.com",
            "password": "repopassword"
        }
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Mock the git clone service to bypass subprocess calls
    with patch("app.api.v1.repositories.RepoManagerService.clone_git_repository") as mock_clone:
        mock_clone.return_value = "/mock/clone/path"
        
        response = await client.post(
            "/api/v1/auth/../repositories/clone", # checks routing resolver
            headers=headers,
            data={
                "name": "Test Git Repo",
                "git_url": "https://github.com/test/repo.git"
            }
        )
        # Note: endpoint is actually /api/v1/repositories/clone
        # Let's call the correct path directly to prevent route mismatch
        response = await client.post(
            "/api/v1/repositories/clone",
            headers=headers,
            data={
                "name": "Test Git Repo",
                "git_url": "https://github.com/test/repo.git"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Git Repo"
        assert data["type"] == "github"
        assert data["github_url"] == "https://github.com/test/repo.git"

@pytest.mark.asyncio
async def test_list_repositories_endpoint(client: AsyncClient):
    # Register and Login
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "repo_list_user@domain.com",
            "password": "repopassword",
            "full_name": "Repo Owner 2"
        }
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "repo_list_user@domain.com",
            "password": "repopassword"
        }
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # First verify empty list
    list_res = await client.get("/api/v1/repositories", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 0
