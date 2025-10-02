#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, inspect, event
from sqlalchemy.engine import Engine

# Add the project root to the Python path
project_root = str(Path(__file__).resolve().parent)
sys.path.append(project_root)

from app.core.config import settings
from app.models.base import Base

# Import models to ensure they are registered with SQLAlchemy
from app.models.user import User
from app.models.document import Document

# Enable foreign key support for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

def init_database():
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
    
    # Create all tables at once to handle relationships properly
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    # Verify tables were created
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    print(f"\nCreated tables: {', '.join(table_names)}")
    
    # Verify table structures
    print("\nVerifying table structures...")
    for table_name in table_names:
        print(f"\nTable: {table_name}")
        columns = inspector.get_columns(table_name)
        for column in columns:
            fk_info = f" (FOREIGN KEY -> {column.get('foreign_keys')})" if column.get('foreign_keys') else ""
            print(f"  {column['name']}: {column['type']}{fk_info}")
    
    print("\nDatabase initialization completed successfully!")

if __name__ == "__main__":
    print("This will recreate your database. All data will be lost!")
    confirm = input("Are you sure you want to continue? (y/n): ")
    if confirm.lower() == 'y':
        init_database()
    else:
        print("Operation cancelled.")
