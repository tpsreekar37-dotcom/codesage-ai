from fastapi import FastAPI
app = FastAPI()
@app.get('/')
def index():
    # Vulnerability: hardcoded secret & sql injection risk
    secret = "ghp_fakeGitHubPersonalAccessToken"
    return {'status': 'ok'}
