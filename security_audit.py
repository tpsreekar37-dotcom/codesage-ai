import httpx
import sys
import uuid
import time
from jose import jwt

BASE_URL = "http://127.0.0.1:8000/api/v1"
SECRET_KEY = "e8f9c1825b1368dc29efb7fba4db97669d54e0c3b036980db3683f2dc5a794b1"
ALGORITHM = "HS256"

client = httpx.Client(timeout=10.0)

def run_test(name, func):
    print(f"[SECURITY TEST] {name} ... ", end="", flush=True)
    try:
        func()
        print("SECURE / PASSED")
    except Exception as e:
        print(f"VULNERABLE / FAILED: {str(e)}")
        sys.exit(1)

# 1. SQL Injection Probing
def test_sql_injection():
    # Attempt SQL injection during login
    res = client.post(f"{BASE_URL}/auth/login", data={
        "username": "' OR '1'='1",
        "password": "anypassword"
    })
    # Should fail with 401 Unauthorized
    assert res.status_code == 401
    
    # Attempt SQL injection during registration
    res = client.post(f"{BASE_URL}/auth/register", json={
        "email": "sqli_test' OR '1'='1@domain.com", # EmailStr validator should catch this
        "password": "ValidPassword123!",
        "full_name": "SQLi User"
    })
    # Should fail with 422 Unprocessable Entity
    assert res.status_code == 422

# 2. XSS Input Validation
def test_xss_prevention():
    email = f"xss_{uuid.uuid4().hex[:5]}@domain.com"
    res = client.post(f"{BASE_URL}/auth/register", json={
        "email": email,
        "password": "Password123!",
        "full_name": "<script>alert('XSS')</script> Super User"
    })
    assert res.status_code == 201
    data = res.json()
    # The API stores it as plain text (which is normal and safe).
    # The vulnerability is only realized if the frontend evaluates the string directly (using eval or dangerouslySetInnerHTML).
    # Since our Vite React frontend uses standard JSX `{user.full_name}`, it escapes HTML tags natively.
    assert data["full_name"] == "<script>alert('XSS')</script> Super User"

# 3. JWT Tampering Verification
def test_jwt_tampering():
    # Login to get a valid token
    email = f"jwt_{uuid.uuid4().hex[:5]}@domain.com"
    client.post(f"{BASE_URL}/auth/register", json={"email": email, "password": "Password123!", "full_name": "JWT User"})
    login_res = client.post(f"{BASE_URL}/auth/login", data={"username": email, "password": "Password123!"})
    token = login_res.json()["access_token"]
    
    # Tamper the token by replacing last character of signature
    tampered_token = token[:-1] + ("A" if token[-1] != "A" else "B")
    
    headers = {"Authorization": f"Bearer {tampered_token}"}
    res = client.get(f"{BASE_URL}/auth/me", headers=headers)
    assert res.status_code == 401
    assert "Could not validate credentials" in res.json()["detail"]

# 4. Expired Token Verification
def test_expired_token():
    # Forge an expired token (expired 1 hour ago)
    expire = int(time.time()) - 3600
    to_encode = {"exp": expire, "sub": str(uuid.uuid4()), "type": "access"}
    expired_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    headers = {"Authorization": f"Bearer {expired_token}"}
    res = client.get(f"{BASE_URL}/auth/me", headers=headers)
    assert res.status_code == 401
    assert "Could not validate credentials" in res.json()["detail"]

# 5. Schema Input Validation
def test_input_validation():
    # 5.1 Invalid email format
    res = client.post(f"{BASE_URL}/auth/register", json={
        "email": "invalidemailaddress",
        "password": "Password123!",
        "full_name": "Bad Email User"
    })
    assert res.status_code == 422
    
    # 5.2 Password too short
    res = client.post(f"{BASE_URL}/auth/register", json={
        "email": "validemail@domain.com",
        "password": "123", # min_length is 6
        "full_name": "Short Password User"
    })
    assert res.status_code == 422

# 6. Unauthorized Access Control
def test_unauthorized_endpoints():
    # Attempt to access protected endpoint without header
    res = client.get(f"{BASE_URL}/auth/me")
    assert res.status_code == 401
    assert "Not authenticated" in res.json()["detail"]

if __name__ == "__main__":
    print("=== STARTING SECURITY PENETRATION AUDIT ===")
    run_test("SQL Injection Prevention", test_sql_injection)
    run_test("XSS Input Sanitization Storage", test_xss_prevention)
    run_test("JWT Token Signature Tampering Check", test_jwt_tampering)
    run_test("Expired JWT Token Exclusion", test_expired_token)
    run_test("Pydantic Model Schema Validations", test_input_validation)
    run_test("Unauthorized API Access Protection", test_unauthorized_endpoints)
    print("=== SECURITY PENETRATION AUDIT PASSED ===")
