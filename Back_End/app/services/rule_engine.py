"""
Module: Timetable Generation & Scheduling (Module 3)
Repository: timeweaver_backend
Owner: Pranathi Nibhanipudi
Epic: 3 - Timetable Generation / Re-generation

RuleEngine Service

Loads, validates, and enforces institutional rules during timetable generation.
Evaluates both hard constraints (must satisfy) and soft constraints (preferences).

Key Functions:
- Load active rules from database
- Validate slot assignments against hard constraints
- Calculate penalty/fitness scores for soft constraints
- Filter applicable rules by department/year

Dependencies:
    - app.models.institutional_rule (InstitutionalRule, RuleType)
    - app.models.timetable (TimetableSlot)

User Stories: 3.3.2, 3.5.2
"""

from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from app.models.institutional_rule import InstitutionalRule, RuleType
from app.models.timetable import TimetableSlot


class RuleEngine:
    """Service for loading and enforcing institutional rules"""
    
    @staticmethod
    def load_active_rules(
        db: Session,
        department_id: Optional[int] = None,
        year_level: Optional[int] = None
    ) -> list[InstitutionalRule]:
        """
        Load all active rules applicable to a department/year.
        
        Args:
            db: Database session
            department_id: Filter by department (None = all)
            year_level: Filter by year level 1-4 (None = all)
            
        Returns:
            List of active InstitutionalRule objects
        """
        stmt = select(InstitutionalRule).where(InstitutionalRule.is_active == True)
        
        rules = list(db.execute(stmt).scalars().all())
        
        # Filter by scope
        filtered = []
        for rule in rules:
            # Check department scope
            if rule.applies_to_departments:
                if department_id and department_id not in rule.applies_to_departments:
                    continue
            
            # Check year scope
            if rule.applies_to_years:
                if year_level and year_level not in rule.applies_to_years:
                    continue
            
            filtered.append(rule)
        
        return filtered
    
    @staticmethod
    def get_hard_constraints(rules: list[InstitutionalRule]) -> list[InstitutionalRule]:
        """Filter for hard constraints only"""
        return [r for r in rules if r.is_hard_constraint]
    
    @staticmethod
    def get_soft_constraints(rules: list[InstitutionalRule]) -> list[InstitutionalRule]:
        """Filter for soft constraints only"""
        return [r for r in rules if not r.is_hard_constraint]
    
    @staticmethod
    def validate_time_window(slot: TimetableSlot, config: dict) -> bool:
        """
        Validate TIME_WINDOW rule.
        
        Config: {"min_slot": 2, "max_slot": 8}
        """
        min_slot = config.get("min_slot", 1)
        max_slot = config.get("max_slot", 10)
        
        return min_slot <= slot.start_slot_id <= max_slot
    
    @staticmethod
    def validate_slot_blackout(slot: TimetableSlot, config: dict) -> bool:
        """
        Validate SLOT_BLACKOUT rule.
        
        Config: {"blackout_slots": [5], "all_days": true}
        """
        blackout_slots = config.get("blackout_slots", [])
        all_days = config.get("all_days", True)
        
        # Check if slot overlaps with blackout
        for offset in range(slot.duration_slots):
            check_slot = slot.start_slot_id + offset
            if check_slot in blackout_slots:
                return False
        
        return True
    
    @staticmethod
    def validate_day_blackout(slot: TimetableSlot, config: dict) -> bool:
        """
        Validate DAY_BLACKOUT rule.
        
        Config: {"blackout_days": [4], "description": "No Friday classes"}
        """
        blackout_days = config.get("blackout_days", [])
        return slot.day_of_week not in blackout_days
    
    @staticmethod
    def validate_max_consecutive(
        db: Session,
        slot: TimetableSlot,
        config: dict,
        all_slots: list[TimetableSlot]
    ) -> bool:
        """
        Validate MAX_CONSECUTIVE rule.
        
        Config: {"max_consecutive_classes": 3}
        
        Note: Requires all slots for the section on that day
        """
        max_consecutive = config.get("max_consecutive_classes", 3)
        
        # Get all slots for this section on this day
        section_day_slots = [
            s for s in all_slots
            if s.section_id == slot.section_id and s.day_of_week == slot.day_of_week
        ]
        
        # Sort by start_slot_id
        section_day_slots.sort(key=lambda s: s.start_slot_id)
        
        # Find consecutive count including new slot
        consecutive_count = 1
        prev_end_slot = slot.start_slot_id + slot.duration_slots - 1
        
        for existing_slot in section_day_slots:
            if existing_slot.id == slot.id:
                continue
            
            existing_end = existing_slot.start_slot_id + existing_slot.duration_slots - 1
            
            # Check if consecutive
            if existing_slot.start_slot_id == prev_end_slot + 1:
                consecutive_count += 1
                prev_end_slot = existing_end
            else:
                consecutive_count = 1
                prev_end_slot = existing_end
            
            if consecutive_count > max_consecutive:
                return False
        
        return True
    
    @staticmethod
    def validate_slot(
        db: Session,
        slot: TimetableSlot,
        rule: InstitutionalRule,
        all_slots: Optional[list[TimetableSlot]] = None
    ) -> bool:
        """
        Validate a timetable slot against a specific rule.
        
        Args:
            db: Database session
            slot: Slot to validate
            rule: Rule to check
            all_slots: All slots (needed for MAX_CONSECUTIVE)
            
        Returns:
            True if slot satisfies the rule
        """
        config = rule.configuration
        
        if rule.rule_type == RuleType.TIME_WINDOW:
            return RuleEngine.validate_time_window(slot, config)
        
        elif rule.rule_type == RuleType.SLOT_BLACKOUT:
            return RuleEngine.validate_slot_blackout(slot, config)
        
        elif rule.rule_type == RuleType.DAY_BLACKOUT:
            return RuleEngine.validate_day_blackout(slot, config)
        
        elif rule.rule_type == RuleType.MAX_CONSECUTIVE:
            if all_slots is None:
                return True  # Can't validate without context
            return RuleEngine.validate_max_consecutive(db, slot, config, all_slots)
        
        # For other types, return True (not implemented yet)
        return True
    
    @staticmethod
    def calculate_soft_constraint_penalty(
        db: Session,
        slot: TimetableSlot,
        rule: InstitutionalRule
    ) -> float:
        """
        Calculate penalty for violating a soft constraint.
        
        Args:
            db: Database session
            slot: Slot to evaluate
            rule: Soft constraint rule
            
        Returns:
            Penalty value (0.0 = satisfied, higher = more violation)
        """
        if rule.is_hard_constraint:
            return 0.0  # Not a soft constraint
        
        config = rule.configuration
        
        # ROOM_PREFERENCE handled separately in ConstraintService
        if rule.rule_type == RuleType.ROOM_PREFERENCE:
            return 0.0
        
        # Other soft constraints TBD
        return 0.0
    
    @staticmethod
    def validate_all_hard_constraints(
        db: Session,
        slot: TimetableSlot,
        rules: list[InstitutionalRule],
        all_slots: Optional[list[TimetableSlot]] = None
    ) -> tuple[bool, list[str]]:
        """
        Validate slot against all hard constraints.
        
        Args:
            db: Database session
            slot: Slot to validate
            rules: List of rules to check
            all_slots: All slots (for context-dependent rules)
            
        Returns:
            (is_valid, list_of_violated_rule_names)
        """
        hard_constraints = RuleEngine.get_hard_constraints(rules)
        violations = []
        
        for rule in hard_constraints:
            if not RuleEngine.validate_slot(db, slot, rule, all_slots):
                violations.append(rule.name)
        
        return len(violations) == 0, violations
