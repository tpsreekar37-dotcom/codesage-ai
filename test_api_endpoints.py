import httpx
import sys
import uuid

BASE_URL = "http://127.0.0.1:8000/api/v1"
test_email = f"qa_test_{uuid.uuid4().hex[:6]}@domain.com"
test_password = "QAPassword123!"
tokens = {}
repo_ids = []
analysis_ids = []

def run_test(name, func):
    print(f"[TEST] {name} ... ", end="", flush=True)
    try:
        func()
        print("PASSED")
    except Exception as e:
        print(f"FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def test_health():
    res = httpx.get("http://127.0.0.1:8000/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"

def test_root():
    res = httpx.get("http://127.0.0.1:8000/")
    assert res.status_code == 200
    assert "Welcome" in res.json()["message"]

def test_register():
    res = httpx.post(f"{BASE_URL}/auth/register", json={
        "email": test_email,
        "password": test_password,
        "full_name": "QA Tester"
    })
    assert res.status_code == 201
    assert res.json()["email"] == test_email

def test_duplicate_register():
    res = httpx.post(f"{BASE_URL}/auth/register", json={
        "email": test_email,
        "password": test_password,
        "full_name": "QA Tester Duplicate"
    })
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]

def test_login():
    res = httpx.post(f"{BASE_URL}/auth/login", data={
        "username": test_email,
        "password": test_password
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    tokens["access"] = data["access_token"]
    tokens["refresh"] = data["refresh_token"]

def test_invalid_login():
    res = httpx.post(f"{BASE_URL}/auth/login", data={
        "username": test_email,
        "password": "WrongPassword123"
    })
    assert res.status_code == 401
    assert "Incorrect email or password" in res.json()["detail"]

def test_get_me():
    headers = {"Authorization": f"Bearer {tokens['access']}"}
    res = httpx.get(f"{BASE_URL}/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == test_email

def test_refresh_token():
    res = httpx.post(f"{BASE_URL}/auth/refresh?refresh_token_in={tokens['refresh']}")
    if res.status_code != 200:
        print(f"\nResponse Code: {res.status_code}")
        print(f"Response Body: {res.text}")
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    tokens["access"] = data["access_token"]
    tokens["refresh"] = data["refresh_token"]

def test_clone_github():
    headers = {"Authorization": f"Bearer {tokens['access']}"}
    res = httpx.post(f"{BASE_URL}/repositories/clone", data={
        "name": "Integration Test Repo",
        "git_url": "https://github.com/octocat/Spoon-Knife.git"
    }, headers=headers)
    if res.status_code != 201:
        print(f"\nResponse Code: {res.status_code}")
        print(f"Response Body: {res.text}")
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Integration Test Repo"
    repo_ids.append(data["id"])

def test_invalid_git_url():
    headers = {"Authorization": f"Bearer {tokens['access']}"}
    res = httpx.post(f"{BASE_URL}/repositories/clone", data={
        "name": "Invalid Git Repo",
        "git_url": "git://github.com/octocat/Spoon-Knife.git" # Invalid URL scheme
    }, headers=headers)
    assert res.status_code == 400

def test_list_repositories():
    headers = {"Authorization": f"Bearer {tokens['access']}"}
    res = httpx.get(f"{BASE_URL}/repositories", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Integration Test Repo"

def test_start_analysis():
    headers = {"Authorization": f"Bearer {tokens['access']}"}
    res = httpx.post(f"{BASE_URL}/analyses", json={
        "repository_id": repo_ids[0]
    }, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["repository_id"] == repo_ids[0]
    assert data["status"] in ["pending", "processing"]
    analysis_ids.append(data["id"])

def test_get_analysis_status():
    headers = {"Authorization": f"Bearer {tokens['access']}"}
    res = httpx.get(f"{BASE_URL}/analyses/{analysis_ids[0]}", headers=headers)
    assert res.status_code == 200
    assert res.json()["id"] == analysis_ids[0]

def test_dashboard_stats():
    headers = {"Authorization": f"Bearer {tokens['access']}"}
    res = httpx.get(f"{BASE_URL}/dashboard/stats", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_repositories" in data
    assert "total_analyses" in data

def test_delete_repository():
    headers = {"Authorization": f"Bearer {tokens['access']}"}
    res = httpx.delete(f"{BASE_URL}/repositories/{repo_ids[0]}", headers=headers)
    assert res.status_code == 200
    assert "successfully deleted" in res.json()["message"]

def test_logout():
    headers = {"Authorization": f"Bearer {tokens['access']}"}
    res = httpx.post(f"{BASE_URL}/auth/logout", headers=headers)
    assert res.status_code == 200
    assert "Successfully logged out" in res.json()["message"]

if __name__ == "__main__":
    print("=== STARTING API ENDPOINT TESTS ===")
    run_test("Healthcheck Endpoint", test_health)
    run_test("Root Welcome Endpoint", test_root)
    run_test("User Registration Endpoint", test_register)
    run_test("Duplicate Email Registration Boundary Check", test_duplicate_register)
    run_test("User Login Endpoint", test_login)
    run_test("Invalid Login Failure Boundary Check", test_invalid_login)
    run_test("Auth Get Current User profile", test_get_me)
    run_test("JWT Token Refresh Lifecycle", test_refresh_token)
    run_test("Repository Clone Endpoint", test_clone_github)
    run_test("Invalid URL Format Input Validation", test_invalid_git_url)
    run_test("Repositories List Retrieve", test_list_repositories)
    run_test("Start AI Analysis Queue", test_start_analysis)
    run_test("Query Analysis Status Endpoint", test_get_analysis_status)
    run_test("Dashboard Statistics Summary", test_dashboard_stats)
    run_test("Repository Delete Cleanup Endpoint", test_delete_repository)
    run_test("User Logout and Session Invalidation", test_logout)
    print("=== ALL API ENDPOINT TESTS PASSED ===")
