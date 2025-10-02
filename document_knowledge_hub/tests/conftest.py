import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

# Import all models to ensure they are registered with SQLAlchemy
from app.models.base import Base
from app.models.user import User
from app.models.document import Document

from app.main import app
from app.db.session import get_db
from app.core.config import settings

# Import all models to ensure they are registered with SQLAlchemy
# This must be done before creating the engine

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create engine with echo=True for debugging
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=True
)

# Create session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables once at the beginning of the test session
@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop all tables after tests complete
    Base.metadata.drop_all(bind=engine)

# Set up the test database session
@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Begin a nested transaction (using SAVEPOINT)
    nested = connection.begin_nested()

    # If the application code calls session.commit, it will end the nested
    # transaction. We need to start a new one when that happens.
    @event.listens_for(session, 'after_transaction_end')
    def restart_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    # Cleanup
    session.close()
    transaction.rollback()
    connection.close()

# Test client with dependency override
@pytest.fixture(scope="function")
def client(db_session):
    # Override the get_db dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    # Apply the override
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up overrides
    app.dependency_overrides.clear()

# Test user data
@pytest.fixture(scope="function")
def test_user():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword"
    }

# Test file data
@pytest.fixture(scope="function")
def test_file():
    # Create a temporary text file for testing
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    try:
        temp_file.write(b"This is a test file content.")
        temp_file.close()
        yield temp_file.name
    finally:
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
