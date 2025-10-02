# tests/test_documents_rate_limit.py
import os
import time
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import get_password_hash
from tests.utils.auth import get_auth_headers

def test_rate_limiting(client: TestClient, test_user: dict, db_session: Session, override_rate_limit):
    settings = override_rate_limit  # Fixture sets RATE_LIMIT_PER_MINUTE=2

    # Create test user
    db_user = User(
        username=test_user["username"],
        email=test_user["email"],
        hashed_password=get_password_hash(test_user["password"])
    )
    db_session.add(db_user)
    db_session.commit()

    headers = get_auth_headers(client, test_user["username"], test_user["password"])
    headers["X-User-ID"] = db_user.username  # unique key for limiter

    # Requests within the limit
    for _ in range(settings.RATE_LIMIT_PER_MINUTE):
        response = client.get("/api/v1/documents", headers=headers)
        assert response.status_code == 200

    # Next request should hit 429
    response = client.get("/api/v1/documents", headers=headers)
    assert response.status_code == 429

    import time
    time.sleep(60)

    # After waiting, request succeeds again
    response = client.get("/api/v1/documents", headers=headers)
    assert response.status_code == 200

