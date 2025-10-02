#!/usr/bin/env python3
import sys
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine

# Add the project root to the Python path
project_root = str(Path(__file__).resolve().parent)
sys.path.append(project_root)

from app.core.config import settings
from app.models.base import Base
from app.models.user import User
from app.models.document import Document

# Enable foreign key support for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

def init_db():
    # Database URL from settings
    db_url = settings.DATABASE_URL
    
    # Create engine with foreign key support
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        echo=True  # Enable SQL logging for debugging
    )
    
    # Drop all tables (if they exist)
    print("Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)
    
    # Create all tables
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    print("\nDatabase initialized successfully!")

if __name__ == "__main__":
    print("This will recreate your database. All data will be lost!")
    confirm = input("Are you sure you want to continue? (y/n): ")
    if confirm.lower() == 'y':
        init_db()
    else:
        print("Operation cancelled.")
