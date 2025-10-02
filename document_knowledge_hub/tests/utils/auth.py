"""Authentication utilities for tests."""
from fastapi.testclient import TestClient

def get_auth_headers(client: TestClient, username: str, password: str) -> dict:
    """Get authentication headers for a test user.
    
    Args:
        client: TestClient instance
        username: Username for authentication
        password: Password for authentication
        
    Returns:
        dict: Headers with Authorization token
    """
    login_data = {
        "username": username,
        "password": password
    }
    # Try both possible login endpoints
    response = client.post(
        "/api/v1/auth/login",
        data=login_data  # Note: Using data= instead of json= for form data
    )
    
    # If token endpoint fails, try login endpoint
    if response.status_code != 200:
        response = client.post(
            "/api/v1/auth/login",
            json=login_data
        )
    
    response.raise_for_status()  # Raise an exception for bad status codes
    token_data = response.json()
    
    # Handle different possible response formats
    token = token_data.get('access_token') or token_data.get('token')
    if not token:
        raise ValueError("No access token found in response")
        
    return {"Authorization": f"Bearer {token}"}
