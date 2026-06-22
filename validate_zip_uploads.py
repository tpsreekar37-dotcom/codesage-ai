import os
import zipfile
import httpx
import sys
import uuid
import time
import io

BASE_URL = "http://127.0.0.1:8000/api/v1"
TEST_PROJECTS_DIR = r"C:\Users\tpvij\Desktop\Google_AI_Code_Review_Platform\test_projects"
os.makedirs(TEST_PROJECTS_DIR, exist_ok=True)

# Define mock contents for 8 project types
PROJECT_TEMPLATES = {
    "python": {
        "ext": ".py", "filename": "app.py", "deps_file": "requirements.txt",
        "deps_content": "fastapi>=0.110.0\npytest>=8.0.0",
        "code": "def process_data(user_input):\n    # Smell: eval usage & unused variable\n    unused_var = 42\n    eval(user_input)\n    for i in range(10):\n        for j in range(10):\n            # Nested loops\n            print(i, j)\n    api_key = \"AIzaSyFakeKey123\" # Hardcoded secret\n"
    },
    "java": {
        "ext": ".java", "filename": "App.java", "deps_file": "pom.xml",
        "deps_content": "<project><modelVersion>4.0.0</modelVersion><artifactId>test-app</artifactId></project>",
        "code": "public class App {\n    private String secret = \"AIzaSyJavaSecretKey\";\n    public void execute(String cmd) {\n        // Bug smell\n        System.out.println(\"cmd: \" + cmd);\n        int[] arr = new int[5];\n        arr[10] = 5; // Array index out of bounds\n    }\n}"
    },
    "cpp": {
        "ext": ".cpp", "filename": "main.cpp", "deps_file": "CMakeLists.txt",
        "deps_content": "cmake_minimum_required(VERSION 3.10)\nadd_executable(app main.cpp)",
        "code": "#include <iostream>\n#include <cstring>\nint main() {\n    char buffer[8];\n    strcpy(buffer, \"This long string overflows buffer!\"); // Stack overflow smell\n    int* leak = new int(10); // Memory leak smell\n    return 0;\n}"
    },
    "javascript": {
        "ext": ".js", "filename": "index.js", "deps_file": "package.json",
        "deps_content": '{"name": "js-app", "dependencies": {}}',
        "code": "const api_key = \"xoxb-fake-slack-token-123456\";\nfunction run() {\n    var x = 10;\n    // Unsafe eval\n    eval('console.log(x)');\n}"
    },
    "typescript": {
        "ext": ".ts", "filename": "index.ts", "deps_file": "package.json",
        "deps_content": '{"name": "ts-app", "devDependencies": {"typescript": "^5.0.0"}}',
        "code": "const secretKey = \"sk_live_stripe_key_12345\";\nexport function calculate(val: number): void {\n    // nested loop\n    for (let i = 0; i < 5; i++) {\n        for (let j = 0; j < 5; j++) {\n            console.log(i + j);\n        }\n    }\n}"
    },
    "react": {
        "ext": ".tsx", "filename": "App.tsx", "deps_file": "package.json",
        "deps_content": '{"name": "react-app", "dependencies": {"react": "^18.2.0"}}',
        "code": "import React, { useEffect, useState } from 'react';\nexport default function App() {\n    const [data, setData] = useState(null);\n    // Infinite re-render loop smell\n    useEffect(() => {\n        setData({});\n    });\n    return <div>React App</div>;\n}"
    },
    "fastapi": {
        "ext": ".py", "filename": "main.py", "deps_file": "requirements.txt",
        "deps_content": "fastapi\nuvicorn",
        "code": "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef index():\n    # Vulnerability: hardcoded secret & sql injection risk\n    secret = \"ghp_fakeGitHubPersonalAccessToken\"\n    return {'status': 'ok'}\n"
    },
    "nodejs": {
        "ext": ".js", "filename": "server.js", "deps_file": "package.json",
        "deps_content": '{"name": "node-app", "dependencies": {"express": "^4.19.0"}}',
        "code": "const express = require('express');\nconst app = express();\n// Resource leak: server listens indefinitely on hardcoded credentials\nconst pwd = 'db_password_12345';\napp.get('/', (req, res) => res.send('Hello'));\n"
    }
}

# Authenticate & get token
def get_auth_token():
    email = f"zip_tester_{uuid.uuid4().hex[:5]}@test.com"
    pwd = "ZipPassword123!"
    httpx.post(f"{BASE_URL}/auth/register", json={"email": email, "password": pwd, "full_name": "ZIP Tester"})
    res = httpx.post(f"{BASE_URL}/auth/login", data={"username": email, "password": pwd})
    return res.json()["access_token"]

def build_project_zip(name, ext, filename, deps_file, deps_content, code):
    proj_dir = os.path.join(TEST_PROJECTS_DIR, name)
    os.makedirs(proj_dir, exist_ok=True)
    
    # Write standard docs
    with open(os.path.join(proj_dir, "README.md"), "w") as f:
        f.write(f"# {name.upper()} Project\nThis is a sample project for code review testing.")
    with open(os.path.join(proj_dir, "LICENSE"), "w") as f:
        f.write("MIT License")
    with open(os.path.join(proj_dir, deps_file), "w") as f:
        f.write(deps_content)
    with open(os.path.join(proj_dir, filename), "w") as f:
        f.write(code)
        
    zip_path = os.path.join(TEST_PROJECTS_DIR, f"{name}.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(proj_dir):
            for file in files:
                file_abs = os.path.join(root, file)
                file_rel = os.path.relpath(file_abs, proj_dir)
                zipf.write(file_abs, file_rel)
                
    return zip_path

def test_zip_scenarios(token):
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n--- Testing Boundary Upload Conditions ---")
    
    # 1. Invalid Format Upload
    txt_file = os.path.join(TEST_PROJECTS_DIR, "invalid_format.txt")
    with open(txt_file, "w") as f:
        f.write("This is not a zip file.")
    with open(txt_file, "rb") as f:
        res = httpx.post(f"{BASE_URL}/repositories/upload", data={"name": "Invalid Format"}, files={"file": f}, headers=headers)
    assert res.status_code == 400
    assert "Only ZIP archives are supported" in res.json()["detail"]
    print("Invalid Format Boundary Check: PASSED")
    
    # 2. Corrupt ZIP File
    corrupt_zip = os.path.join(TEST_PROJECTS_DIR, "corrupt.zip")
    with open(corrupt_zip, "wb") as f:
        f.write(b"PK\x03\x04corruptedbyteshere1234567890")
    with open(corrupt_zip, "rb") as f:
        res = httpx.post(f"{BASE_URL}/repositories/upload", data={"name": "Corrupt Zip"}, files={"file": f}, headers=headers)
    assert res.status_code == 400
    assert "Corrupt or invalid ZIP archive file" in res.json()["detail"]
    print("Corrupt ZIP Boundary Check: PASSED")
    
    # 3. Path Traversal ZIP File
    traversal_zip = os.path.join(TEST_PROJECTS_DIR, "traversal.zip")
    with zipfile.ZipFile(traversal_zip, 'w') as zipf:
        # Write file with ../ path structure
        zipf.writestr("../../etc/passwd", "malicious content")
    with open(traversal_zip, "rb") as f:
        res = httpx.post(f"{BASE_URL}/repositories/upload", data={"name": "Traversal Zip"}, files={"file": f}, headers=headers)
    assert res.status_code == 400
    assert "directory traversal" in res.json()["detail"].lower()
    print("Path Traversal Escape Prevention: PASSED")

    # 4. Large File (exceeding 25MB)
    large_zip = os.path.join(TEST_PROJECTS_DIR, "large.zip")
    # Write a zip file with a large dummy payload (26MB)
    large_dummy_file = os.path.join(TEST_PROJECTS_DIR, "dummy_26MB.txt")
    with open(large_dummy_file, "wb") as f:
        f.seek(26 * 1024 * 1024 - 1)
        f.write(b"\0")
    with zipfile.ZipFile(large_zip, 'w') as zipf:
        zipf.write(large_dummy_file, "large_file.txt")
    
    # Remove temporary dummy file to save space
    os.remove(large_dummy_file)
    
    with open(large_zip, "rb") as f:
        res = httpx.post(f"{BASE_URL}/repositories/upload", data={"name": "Large Zip"}, files={"file": f}, headers=headers)
    # The middleware or file streamer should intercept and raise 413
    assert res.status_code == 413
    assert "exceeds maximum allowed size" in res.json()["detail"]
    print("File Upload Max Size Limit Enforcement: PASSED")
    
    # Clean up test files
    for f_path in [txt_file, corrupt_zip, traversal_zip, large_zip]:
        if os.path.exists(f_path):
            os.remove(f_path)

def test_language_projects(token):
    headers = {"Authorization": f"Bearer {token}"}
    print("\n--- Generating & Uploading 8 Language Projects ---")
    
    for name, t in PROJECT_TEMPLATES.items():
        zip_path = build_project_zip(name, t["ext"], t["filename"], t["deps_file"], t["deps_content"], t["code"])
        
        # Upload
        print(f"Uploading {name.upper()} zip ... ", end="", flush=True)
        with open(zip_path, "rb") as f:
            res = httpx.post(f"{BASE_URL}/repositories/upload", data={"name": f"{name.upper()} Smells Project"}, files={"file": f}, headers=headers)
        assert res.status_code == 201
        repo_id = res.json()["id"]
        print("UPLOADED")
        
        # Trigger Analysis
        print(f"Triggering analysis for {name.upper()} ... ", end="", flush=True)
        analysis_res = httpx.post(f"{BASE_URL}/analyses", json={"repository_id": repo_id}, headers=headers)
        assert analysis_res.status_code == 201
        analysis_id = analysis_res.json()["id"]
        print("QUEUED")
        
        # Poll analysis status
        print("Waiting for review completion ... ", end="", flush=True)
        completed = False
        for _ in range(20): # poll for max 20 seconds
            status_res = httpx.get(f"{BASE_URL}/analyses/{analysis_id}", headers=headers)
            status = status_res.json()["status"]
            if status == "completed":
                completed = True
                break
            elif status == "failed":
                print(f"FAILED (error: {status_res.json().get('error_message')})")
                sys.exit(1)
            time.sleep(1)
            
        assert completed, "Analysis did not complete within timeout limits."
        print("COMPLETED")
        
        # Retrieve report
        report_res = httpx.get(f"{BASE_URL}/reports/analysis/{analysis_id}", headers=headers)
        assert report_res.status_code == 200
        report = report_res.json()
        assert report["score_quality"] >= 0
        assert len(report["markdown_content"]) > 0
        print(f"Score Quality: {report['score_quality']}/100 | Findings Count: {len(report['findings'])}")
        print("-" * 40)

if __name__ == "__main__":
    print("=== STARTING ZIP AUTOMATED VALIDATIONS ===")
    token = get_auth_token()
    test_zip_scenarios(token)
    test_language_projects(token)
    print("=== ALL ZIP FEATURE VALIDATIONS PASSED ===")
