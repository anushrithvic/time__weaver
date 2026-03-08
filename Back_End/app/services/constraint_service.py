"""
Module: Timetable Generation & Scheduling (Module 3)
Repository: timeweaver_backend
Owner: Pranathi Nibhanipudi
Epic: 3 - Timetable Generation / Re-generation

Constraint Service - Validation and Weight Calculation

Validates hard constraints (must be satisfied) and calculates soft constraint
weights for optimization.

Hard Constraints:
- Room capacity >= Section student count
- Lab courses → Lab rooms only
- PE/FE synchronization (same time for all sections in same year/dept)

Soft Constraints (weights 0-1):
- Home room preference: 0.9 weight
- Faculty preference: 0.8 weight

Dependencies:
    - app.models.room (Room model)
    - app.models.section (Section model)
    - app.models.course (Course model)
    - app.models.timetable (TimetableSlot model)

User Stories: 3.4.2 (ML-Based Learning), 3.3.2 (Multi-Solution)
"""

from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from app.models.room import Room
from app.models.section import Section
from app.models.course import Course
from app.models.timetable import TimetableSlot
from app.services.rule_engine import RuleEngine


class ConstraintService:
    """Service for constraint validation and scoring"""
    
    def __init__(self, db: Session):
        """
        Initialize with database session.
        
        Args:
            db: Database session for loading rules
        """
        self.db = db
        self.rules = RuleEngine.load_active_rules(db)
    
    # Soft constraint weights
    HOME_ROOM_WEIGHT = 0.9
    FACULTY_PREFERENCE_WEIGHT = 0.8
    
    @staticmethod
    def check_room_capacity(room: Room, section: Section) -> bool:
        """
        HARD CONSTRAINT: Room capacity must accommodate section size.
        
        Args:
            room: Room being assigned
            section: Section being scheduled
            
        Returns:
            True if room capacity >= student count
        """
        return room.capacity >= section.student_count
    
    @staticmethod
    def check_lab_requirement(room: Room, course: Course) -> bool:
        """
        HARD CONSTRAINT: Lab courses must be in lab rooms.
        
        Args:
            room: Room being assigned
            course: Course being scheduled
            
        Returns:
            True if constraint satisfied
        """
        if course.requires_lab:
            return room.room_type == 'lab' and room.has_lab_equipment
        return True  # Non-lab courses can be anywhere
    
    @staticmethod
    def get_home_room_score(room: Room, section: Section) -> float:
        """
        SOFT CONSTRAINT: Prefer section's dedicated home room.
        
        Args:
            room: Room being assigned
            section: Section being scheduled
            
        Returns:
            Weight (0.9 if home room, 0.0 otherwise)
        """
        if section.dedicated_room_id and room.id == section.dedicated_room_id:
            return ConstraintService.HOME_ROOM_WEIGHT
        return 0.0
    
    @staticmethod
    def validate_room_assignment(
        room: Room,
        section: Section,
        course: Course
    ) -> dict[str, any]:
        """
        Validate all room-related constraints.
        
        Args:
            room: Room to validate
            section: Section being scheduled
            course: Course being taught
            
        Returns:
            Dict with validation results
        """
        # Check hard constraints
        capacity_ok = ConstraintService.check_room_capacity(room, section)
        lab_ok = ConstraintService.check_lab_requirement(room, course)
        
        # Calculate soft constraint score
        home_room_score = ConstraintService.get_home_room_score(room, section)
        
        return {
            "valid": capacity_ok and lab_ok,
            "capacity_satisfied": capacity_ok,
            "lab_requirement_satisfied": lab_ok,
            "home_room_score": home_room_score,
            "total_soft_score": home_room_score
        }
    
    @staticmethod
    def check_elective_synchronization(
        db: Session,
        slots: list[TimetableSlot],
        elective_group_id: int,
        department_id: int,
        year_level: int
    ) -> bool:
        """
        HARD CONSTRAINT: All PE/FE courses in same group must be scheduled
        at the same time for synchronization.
        
        Args:
            db: Database session
            slots: Existing timetable slots
            elective_group_id: Elective group (PE1, PE2, FE1)
            department_id: Department
            year_level: Year level
            
        Returns:
            True if all slots for this elective are synchronized
        """
        # Get all slots for this elective group
        elective_slots = [
            slot for slot in slots
            if slot.course and slot.course.elective_group_id == elective_group_id
        ]
        
        if not elective_slots:
            return True  # No conflicts if no slots
        
        # Check if all have same start_slot_id and day_of_week
        first_slot = elective_slots[0]
        return all(
            slot.start_slot_id == first_slot.start_slot_id and
            slot.day_of_week == first_slot.day_of_week
            for slot in elective_slots
        )
    
    @staticmethod
    def validate_multislot_course(
        slot: TimetableSlot,
        max_slots_per_day: int = 8
    ) -> bool:
        """
        HARD CONSTRAINT: Multi-slot courses (CIR) must fit within day.
        
        Args:
            slot: TimetableSlot with duration_slots
            max_slots_per_day: Maximum slots in a day
            
        Returns:
            True if course fits within day
        """
        end_slot = slot.start_slot_id + slot.duration_slots - 1
        return end_slot <= max_slots_per_day
    
    @staticmethod
    def validate_batching_config(
        section_size: int,
        num_batches: int,
        batch_size: int
    ) -> bool:
        """
        HARD CONSTRAINT: Batching config must accommodate all students.
        
        Args:
            section_size: Total students in section
            num_batches: Number of batches
            batch_size: Students per batch
            
        Returns:
            True if num_batches * batch_size >= section_size
        """
        total_capacity = num_batches * batch_size
        return total_capacity >= section_size
    
    @staticmethod
    def calculate_slot_fitness(
        room: Room,
        section: Section,
        course: Course
    ) -> float:
        """
        Calculate overall fitness score for a slot assignment.
        
        Args:
            room: Assigned room
            section: Section
            course: Course
            
        Returns:
            Fitness score (0.0-1.0, higher is better)
        """
        validation = ConstraintService.validate_room_assignment(
            room, section, course
        )
        
        if not validation["valid"]:
            return 0.0  # Hard constraint violation
        
        # Return soft constraint score
        return validation["total_soft_score"]
    
    def validate_slot_with_rules(
        self,
        slot: TimetableSlot,
        all_slots: Optional[list[TimetableSlot]] = None
    ) -> dict:
        """
        Validate slot against all institutional rules.
        
        Args:
            slot: TimetableSlot to validate
            all_slots: All slots (for context-dependent rules)
            
        Returns:
            Dict with validation results and violations
        """
        is_valid, violations = RuleEngine.validate_all_hard_constraints(
            self.db,
            slot,
            self.rules,
            all_slots
        )
        
        return {
            "valid": is_valid,
            "violations": violations,
            "rules_checked": len(self.rules)
        }
