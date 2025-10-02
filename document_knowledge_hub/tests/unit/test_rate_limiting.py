import os
from importlib import reload

from fastapi import status
from time import sleep

from tests.utils.auth import get_auth_headers

# Test rate limiting
def test_rate_limiting(client, test_user, db_session):
    # Create a test user
    from app.models.user import User
    from app.core.security import get_password_hash
    from app.core import config
    
    db_user = User(
        username=test_user["username"],
        email=test_user["email"],
        hashed_password=get_password_hash(test_user["password"])
    )
    db_session.add(db_user)
    db_session.commit()
    
    # Get auth headers
    headers = get_auth_headers(client, test_user["username"], test_user["password"])
    os.environ["RATE_LIMIT_PER_MINUTE"] = "2"
    reload(config)

    from app.core.config import settings
    
    # Make requests (just under the limit)
    for _ in range(settings.RATE_LIMIT_PER_MINUTE):
        response = client.get(
            "/api/v1/documents",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
    
    # The next request should be rate limited
    response = client.get(
        "/api/v1/documents",
        headers=headers
    )
    
    # The exact status code might vary based on your rate limiting implementation
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    
    # Wait for rate limit to reset (assuming 1-minute window)
    sleep(60)
    
    # Should work again after waiting
    response = client.get(
        "/api/v1/documents",
        headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
