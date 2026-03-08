"""
Seed script for default institutional rules.

Creates 5 default rules:
1. Business Hours - TIME_WINDOW
2. Lunch Break - SLOT_BLACKOUT
3. Max 3 Consecutive - MAX_CONSECUTIVE
4. Home Room Preference - ROOM_PREFERENCE (soft)
5. No Friday Year 4 - DAY_BLACKOUT (example)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.institutional_rule import InstitutionalRule, RuleType
from app.core.config import settings


def seed_default_rules():
    """Seed default institutional rules"""
    sync_database_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(sync_database_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    default_rules = [
        {
            "name": "Business Hours Only",
            "description": "Classes only between 9 AM - 5 PM (slots 2-8)",
            "rule_type": RuleType.TIME_WINDOW,
            "configuration": {"min_slot": 2, "max_slot": 8},
            "is_hard_constraint": True,
            "weight": 1.0,
            "is_active": True
        },
        {
            "name": "Lunch Break",
            "description": "Slot 5 (1-2 PM) reserved for lunch",
            "rule_type": RuleType.SLOT_BLACKOUT,
            "configuration": {"blackout_slots": [5], "all_days": True},
            "is_hard_constraint": True,
            "weight": 1.0,
            "is_active": True
        },
        {
            "name": "Max 3 Consecutive Classes",
            "description": "Students cannot have more than 3 consecutive classes",
            "rule_type": RuleType.MAX_CONSECUTIVE,
            "configuration": {"max_consecutive_classes": 3},
            "is_hard_constraint": True,
            "weight": 1.0,
            "is_active": True
        },
        {
            "name": "Home Room Preference",
            "description": "Prefer section's dedicated room (90% weight)",
            "rule_type": RuleType.ROOM_PREFERENCE,
            "configuration": {"preference_weight": 0.9},
            "is_hard_constraint": False,
            "weight": 0.9,
            "is_active": True
        },
        {
            "name": "No Friday Year 4 Example",
            "description": "Example: No classes on Friday for Year 4 students",
            "rule_type": RuleType.DAY_BLACKOUT,
            "configuration": {"blackout_days": [4]},  # 4 = Friday
            "is_hard_constraint": False,
            "weight": 0.7,
            "applies_to_years": [4],
            "is_active": False  # Disabled by default
        }
    ]
    
    for rule_data in default_rules:
        # Check if exists
        existing = db.query(InstitutionalRule).filter(
            InstitutionalRule.name == rule_data["name"]
        ).first()
        
        if not existing:
            rule = InstitutionalRule(**rule_data)
            db.add(rule)
            print(f"✅ Created rule: {rule_data['name']}")
        else:
            print(f"⏭️  Rule already exists: {rule_data['name']}")
    
    db.commit()
    db.close()
    engine.dispose()
    print("\n🎉 Default rules seeded successfully!")

if __name__ == "__main__":
    seed_default_rules()
