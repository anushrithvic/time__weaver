"""
Direct table creation for FacultyLeave

Bypasses Alembic if needed.
Creates table directly using SQLAlchemy.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from app.models.faculty_leave import FacultyLeave
from app.db.base import Base
from app.core.config import settings

def create_faculty_leaves_table():
    """Create faculty_leaves table directly"""
    
    # Create synchronous engine for table creation
    sync_database_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(sync_database_url)
    
    # Create enums if not exist
    with engine.connect() as conn:
        conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE leavetype AS ENUM (
                    'SICK', 'CASUAL', 'MATERNITY', 'PATERNITY', 'SABBATICAL',
                    'STUDY', 'EMERGENCY', 'OTHER'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))
        
        conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE leavestrategy AS ENUM (
                    'WITHIN_SECTION_SWAP', 'REDISTRIBUTE', 'REPLACEMENT', 'CANCEL', 'MANUAL'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))
        
        conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE leavestatus AS ENUM (
                    'PROPOSED', 'APPROVED', 'APPLIED', 'REJECTED', 'CANCELLED'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))
        
        conn.commit()
        print("✅ Created leave enums")
    
    # Create table
    FacultyLeave.__table__.create(engine, checkfirst=True)
    print("✅ Created faculty_leaves table")
    
    engine.dispose()

if __name__ == "__main__":
    create_faculty_leaves_table()
    print("\n🎉 Table created successfully!")
