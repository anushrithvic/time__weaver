"""
Module: Timetable Generation & Scheduling (Module 3)
Repository: timeweaver_backend
Owner: Pranathi Nibhanipudi
Epic: 3 - Timetable Generation / Re-generation

Institutional Rules Model

User-configurable institutional constraints and rules that govern
timetable generation. Supports flexible JSON-based configuration
for any type of rule.

Rule Types:
- TIME_WINDOW: Restrict class timings
- SLOT_BLACKOUT: Reserve slots (e.g., lunch break)
- MAX_CONSECUTIVE: Limit consecutive classes
- ELECTIVE_SYNC: Force elective synchronization
- FACULTY_WORKLOAD: Faculty hour limits
- ROOM_PREFERENCE: Home room soft constraints
- DAY_BLACKOUT: No classes on certain days
- CUSTOM: Admin-defined logic

Dependencies:
    - app.db.base (Base class)
    - sqlalchemy (Column types)

User Stories: 3.3.2 (Multi-Solution), 3.5.2 (Multi-Objective)
"""

import enum
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, JSON
from sqlalchemy.dialects.postgresql import ARRAY, ENUM as SQLEnum
from sqlalchemy.sql import func
from app.db.session import Base


class RuleType(str, enum.Enum):
    """Types of institutional rules"""
    TIME_WINDOW = "TIME_WINDOW"              # "No classes before 9 AM"
    SLOT_BLACKOUT = "SLOT_BLACKOUT"          # "Slot 5 = lunch break"
    MAX_CONSECUTIVE = "MAX_CONSECUTIVE"      # "Max 3 consecutive classes"
    ELECTIVE_SYNC = "ELECTIVE_SYNC"          # "PE must sync across sections"
    FACULTY_WORKLOAD = "FACULTY_WORKLOAD"    # "Max 18 hours/week"
    ROOM_PREFERENCE = "ROOM_PREFERENCE"      # "Home room preference weight"
    DAY_BLACKOUT = "DAY_BLACKOUT"            # "No Friday classes for Year 4"
    CUSTOM = "CUSTOM"                         # Admin-defined logic


class InstitutionalRule(Base):
    """
    User-configurable institutional constraints and rules.
    
    Supports flexible JSON-based configuration for any type of rule.
    Can be hard constraints (must satisfy) or soft constraints (preferences).
    
    Attributes:
        id (int): Primary key
        name (str): Unique rule name
        description (str): Human-readable description
        rule_type (RuleType): Type of rule
        configuration (dict): JSON configuration (rule-specific)
        is_hard_constraint (bool): Hard (must satisfy) vs soft (preference)
        weight (float): Weight for soft constraints (0.0-1.0)
        applies_to_departments (list[int]): Department IDs (empty = all)
        applies_to_years (list[int]): Year levels 1-4 (empty = all)
        is_active (bool): Whether rule is enabled
        created_at (datetime): Creation timestamp
        
    Configuration Examples:
        TIME_WINDOW: {"min_slot": 2, "max_slot": 8}
        SLOT_BLACKOUT: {"blackout_slots": [5], "all_days": true}
        MAX_CONSECUTIVE: {"max_consecutive_classes": 3}
        ROOM_PREFERENCE: {"preference_weight": 0.9}
    """
    __tablename__ = "institutional_rules"
    
    # Core Fields
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    rule_type = Column(String, nullable=False, index=True)
    
    # Flexible JSON configuration (rule-specific)
    configuration = Column(JSON, nullable=False)
    
    # Constraint classification
    is_hard_constraint = Column(Boolean, nullable=False, default=True)
    weight = Column(Float, nullable=False, default=1.0)  # For soft constraints (0.0-1.0)
    
    # Scope (empty arrays = applies to all)
    applies_to_departments = Column(ARRAY(Integer), default=list)
    applies_to_years = Column(ARRAY(Integer), default=list)  # 1, 2, 3, or 4
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<InstitutionalRule(id={self.id}, name='{self.name}', type={self.rule_type}, active={self.is_active})>"
