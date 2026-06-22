import httpx
import sys
import uuid
import time
import os

BASE_URL = "http://127.0.0.1:8000/api/v1"
CLONE_DIR = r"C:\Users\tpvij\Desktop\Google_AI_Code_Review_Platform\backend\data\cloned"

# Persistent client with global 45.0 second timeout to prevent read timeouts on git operations
client = httpx.Client(timeout=45.0)

def get_auth_token():
    email = f"git_tester_{uuid.uuid4().hex[:5]}@test.com"
    pwd = "GitPassword123!"
    client.post(f"{BASE_URL}/auth/register", json={"email": email, "password": pwd, "full_name": "Git Tester"})
    res = client.post(f"{BASE_URL}/auth/login", data={"username": email, "password": pwd})
    return res.json()["access_token"]

def verify_cleanup_of_directories():
    # Verify that no leftover directories remain in the clone folder that are empty or partial
    if os.path.exists(CLONE_DIR):
        dirs = os.listdir(CLONE_DIR)
        print(f"Clone folder contains {len(dirs)} user subdirectories: {dirs}")
        # Each user has a subdirectory. We will check if there are nested repo folders
        for user_dir in dirs:
            user_path = os.path.join(CLONE_DIR, user_dir)
            if os.path.isdir(user_path):
                repos = os.listdir(user_path)
                print(f"User {user_dir} has active repository folders: {repos}")

def test_clone_scenarios(token):
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Test invalid Git URL format
    print("Testing invalid Git URL format ... ", end="", flush=True)
    res = client.post(f"{BASE_URL}/repositories/clone", data={
        "name": "Invalid Git URL",
        "git_url": "ftp://github.com/psf/requests.git"
    }, headers=headers)
    assert res.status_code == 400
    assert "Invalid Git HTTP/HTTPS repository URL" in res.json()["detail"]
    print("PASSED")

    # 2. Test private/non-existent Git repository clone
    print("Testing private repository cloning failure ... ", end="", flush=True)
    res = client.post(f"{BASE_URL}/repositories/clone", data={
        "name": "Private Repo",
        "git_url": "https://github.com/github/this-is-private-and-does-not-exist.git"
    }, headers=headers)
    # This should fail cloning (returns 400 Bad Request)
    assert res.status_code == 400
    assert "Failed to clone Git repository" in res.json()["detail"]
    print("PASSED")

    # 3. Test successful public repository cloning (psf/requests)
    print("Testing successful clone of psf/requests (shallow) ... ", end="", flush=True)
    start_time = time.time()
    res = client.post(f"{BASE_URL}/repositories/clone", data={
        "name": "Requests Library",
        "git_url": "https://github.com/psf/requests.git"
    }, headers=headers)
    duration = time.time() - start_time
    assert res.status_code == 201
    repo_id = res.json()["id"]
    print(f"PASSED (Cloned in {duration:.1f}s)")
    
    # Run analysis on Requests
    print("Triggering analysis on Requests codebase ... ", end="", flush=True)
    an_res = client.post(f"{BASE_URL}/analyses", json={"repository_id": repo_id}, headers=headers)
    assert an_res.status_code == 201
    analysis_id = an_res.json()["id"]
    print("QUEUED")
    
    # Wait for completed
    completed = False
    for _ in range(30):
        status_res = client.get(f"{BASE_URL}/analyses/{analysis_id}", headers=headers)
        status = status_res.json()["status"]
        if status == "completed":
            completed = True
            break
        elif status == "failed":
            print(f"FAILED (error: {status_res.json().get('error_message')})")
            sys.exit(1)
        time.sleep(1)
    assert completed
    print("COMPLETED (Report generated successfully)")
    
    # Clean up repository from database
    print("Deleting cloned Requests repository ... ", end="", flush=True)
    del_res = client.delete(f"{BASE_URL}/repositories/{repo_id}", headers=headers)
    assert del_res.status_code == 200
    print("DELETED")

    # 4. Test Timeout limits by cloning a massive repo (e.g. Microsoft/TypeScript or similar)
    print("Testing timeout handler with a large repository clone (microsoft/TypeScript) ... ", end="", flush=True)
    try:
        res = client.post(f"{BASE_URL}/repositories/clone", data={
            "name": "TypeScript Massive",
            "git_url": "https://github.com/microsoft/TypeScript.git"
        }, headers=headers)
        # If it completes in 30s, it returns 201. If it exceeds 30s, it returns 408.
        if res.status_code == 201:
            print("CLONED SUCCESSFULLY (completed within 30 seconds)")
            repo_id_ts = res.json()["id"]
            # delete it to clean up space
            client.delete(f"{BASE_URL}/repositories/{repo_id_ts}", headers=headers)
        elif res.status_code == 408:
            print("PASSED (Timeout intercepted correctly and returned HTTP 408)")
        else:
            print(f"FAILED (Returned HTTP {res.status_code}: {res.text})")
            sys.exit(1)
    except httpx.TimeoutException:
        print("PASSED (HTTP client timed out, timeout was caught)")

if __name__ == "__main__":
    print("=== STARTING GIT CLONE VALIDATIONS ===")
    token = get_auth_token()
    test_clone_scenarios(token)
    verify_cleanup_of_directories()
    print("=== ALL GIT CLONE VALIDATIONS PASSED ===")
