from contextlib import contextmanager
from typing import Generator, Any

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, Session as SessionType

from ..core.config import settings

def setup_sqlite_pragmas(dbapi_connection: Any, _) -> None:
    """Configure SQLite pragmas for better performance and reliability."""
    if dbapi_connection is None:
        return
        
    # Enable foreign keys
    dbapi_connection.execute("PRAGMA foreign_keys=ON")
    # Enable Write-Ahead Logging for better concurrency
    dbapi_connection.execute("PRAGMA journal_mode=WAL")
    # Set busy timeout to 30 seconds
    dbapi_connection.execute("PRAGMA busy_timeout=30000")
    # Better performance for SQLite
    dbapi_connection.execute("PRAGMA synchronous=NORMAL")
    # Increase cache size (in pages, 2000 pages = 2MB)
    dbapi_connection.execute("PRAGMA cache_size=2000")
    # Allow SQLite to use memory for temporary storage
    dbapi_connection.execute("PRAGMA temp_store=MEMORY")

# Create engine with configuration
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    connect_args={
        "check_same_thread": False,  # Required for SQLite with multiple threads
        "timeout": 30,  # 30 seconds timeout for database operations
    },
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=settings.SQL_ECHO,  # Enable SQL query logging based on settings
    future=True  # Use SQLAlchemy 2.0 style APIs
)

# Apply SQLite pragmas when a connection is created
if "sqlite" in str(settings.SQLALCHEMY_DATABASE_URI):
    event.listen(engine, "connect", setup_sqlite_pragmas)
    
    # Apply WAL mode and other settings if they weren't set in the event
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL"))
        conn.execute(text("PRAGMA foreign_keys=ON"))

# Create session factory with scoped_session for thread safety
SessionFactory = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True  # Use SQLAlchemy 2.0 style
)

# Scoped session for thread safety
SessionLocal = scoped_session(SessionFactory)

# Base class for all models
Base = declarative_base()

# @contextmanager
def get_db() -> Generator[SessionType, None, None]:
    """
    Dependency function that yields database sessions.
    Handles session lifecycle including rollback on exceptions.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def close_db_connection() -> None:
    """Close all database connections."""
    try:
        SessionLocal.remove()
        engine.dispose()
    except Exception as e:
        print(f"Error closing database connections: {e}")
