"""
Direct table creation for InstitutionalRule

Bypasses Alembic due to AsyncEngine issues.
Creates table directly using SQL Alchemy.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from app.models.institutional_rule import InstitutionalRule, RuleType
from app.db.base import Base
from app.core.config import settings

def create_institutional_rules_table():
    """Create institutional_rules table directly"""
    
    # Create synchronous engine for  table creation
    sync_database_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(sync_database_url)
    
    # Create enum if not exists
    with engine.connect() as conn:
        conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE institutionalruletype AS ENUM (
                    'TIME_WINDOW', 'SLOT_BLACKOUT', 'MAX_CONSECUTIVE', 'ELECTIVE_SYNC',
                    'FACULTY_WORKLOAD', 'ROOM_PREFERENCE', 'DAY_BLACKOUT', 'CUSTOM'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))
        conn.commit()
        print("✅ Created institutionalruletype enum")
    
    # Create table
    InstitutionalRule.__table__.create(engine, checkfirst=True)
    print("✅ Created institutional_rules table")
    
    engine.dispose()

if __name__ == "__main__":
    create_institutional_rules_table()
    print("\n🎉 Table created successfully!")
