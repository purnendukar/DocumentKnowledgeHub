from fastapi.testclient import TestClient
from app.main import app
import base64

client = TestClient(app)

def test_register_login_and_upload_search():
    # register
    resp = client.post("/auth/register", json={"username": "alice", "password": "password123"})
    assert resp.status_code == 200
    # login
    resp = client.post("/auth/login", data={"username": "alice", "password": "password123"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # upload small txt
    files = {"file": ("hello.txt", b"Hello world, this is a test document.", "text/plain")}
    resp = client.post("/docs/upload", files=files, headers=headers)
    assert resp.status_code == 200
    doc_id = resp.json()["id"]

    # search
    resp = client.get("/docs/search?q=Hello", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # metadata
    resp = client.get(f"/docs/metadata/{doc_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["filename"] == "hello.txt"
