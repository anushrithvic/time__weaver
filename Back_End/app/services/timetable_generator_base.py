"""
Module: Timetable Generation & Scheduling (Module 3)
Repository: timeweaver_backend
Owner: Pranathi Nibhanipudi
Epic: 3 - Timetable Generation / Re-generation

Timetable Generator Base Service

Provides core functionality for all timetable generation algorithms:
- Empty timetable initialization
- Slot assignment and validation
- Fitness calculation
- Solution ranking

Dependencies:
    - app.models.timetable (Timetable, TimetableSlot)
    - app.models.semester (Semester)
    - app.models.section (Section)
    - app.models.room (Room)
    - app.models.course (Course)
    - app.models.time_slot(TimeSlot)
    - app.services.curriculum_service (CurriculumService)
    - app.services.constraint_service (ConstraintService)
    - app.services.conflict_detector (ConflictDetector)

User Stories: 3.3.2 (Multi-Solution Generation)
"""

import random
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.timetable import Timetable, TimetableSlot
from app.models.semester import Semester
from app.models.section import Section
from app.models.room import Room
from app.models.course import Course
from app.models.time_slot import TimeSlot
from app.services.curriculum_service import CurriculumService
from app.services.constraint_service import ConstraintService
from app.services.conflict_detector import ConflictDetector


class TimetableGeneratorBase:
    """Base class for timetable generation algorithms"""
    
    def __init__(self, db: Session):
        self.db = db
        self.curriculum_service = CurriculumService()
        self.constraint_service = ConstraintService()
        self.conflict_detector = ConflictDetector()
    
    def initialize_empty_timetable(
        self,
        semester_id: int,
        name: str,
        algorithm: str = "UNKNOWN"
    ) -> Timetable:
        """
        Create an empty timetable for a semester.
        
        Args:
            semester_id: Semester to generate for
            name: Timetable name
            algorithm: Generation algorithm name
            
        Returns:
            Empty Timetable object
        """
        timetable = Timetable(
            semester_id=semester_id,
            name=name,
            status="generating",
            conflict_count=0,
            quality_score=0.0,
            is_published=False,
            generation_algorithm=algorithm,
            created_at=datetime.now(timezone.utc)
        )
        
        self.db.add(timetable)
        self.db.commit()
        self.db.refresh(timetable)
        
        return timetable
    
    def create_slot_assignment(
        self,
        timetable_id: int,
        section_id: int,
        course_id: int,
        room_id: int,
        start_slot_id: int,
        day_of_week: int,
        duration_slots: int = 1,
        primary_faculty_id: Optional[int] = None,
        batch_number: Optional[int] = None
    ) -> TimetableSlot:
        """
        Create a timetable slot assignment.
        
        Args:
            timetable_id: Timetable ID
            section_id: Section being scheduled
            course_id: Course being taught
            room_id: Room assigned
            start_slot_id: Starting time slot
            day_of_week: Day (0=Monday, 6=Sunday)
            duration_slots: Number of consecutive slots
            primary_faculty_id: Instructor
            batch_number: Lab batch number
            
        Returns:
            TimetableSlot object
        """
        slot = TimetableSlot(
            timetable_id=timetable_id,
            section_id=section_id,
            course_id=course_id,
            room_id=room_id,
            start_slot_id=start_slot_id,
            duration_slots=duration_slots,
            day_of_week=day_of_week,
            primary_faculty_id=primary_faculty_id,
            batch_number=batch_number,
            is_locked=False
        )
        
        self.db.add(slot)
        return slot
    
    def calculate_fitness(self, timetable_id: int) -> float:
        """
        Calculate fitness score for a timetable (0.0-1.0, higher is better).
        
        Fitness combines:
        - Hard constraint violations (conflicts): -1.0 per conflict
        - Soft constraint satisfaction: +0.0 to +1.0
        
        Args:
            timetable_id: Timetable to evaluate
            
        Returns:
            Fitness score (0.0-1.0)
        """
        # Detect conflicts
        conflicts = self.conflict_detector.detect_all_conflicts(self.db, timetable_id)
        
        # Get all slots
        stmt = select(TimetableSlot).where(TimetableSlot.timetable_id == timetable_id)
        slots = list(self.db.execute(stmt).scalars().all())
        
        if not slots:
            return 0.0
        
        # Hard constraint penalty
        conflict_penalty = len(conflicts) * 0.1
        
        # Soft constraint score (home room preference)
        soft_score = 0.0
        for slot in slots:
            section = self.db.get(Section, slot.section_id)
            room = self.db.get(Room, slot.room_id)
            
            if section and room:
                soft_score += self.constraint_service.get_home_room_score(room, section)
        
        # Normalize soft score
        avg_soft_score = soft_score / len(slots) if slots else 0.0
        
        # Final fitness: penalize conflicts, reward soft constraints
        fitness = max(0.0, min(1.0, avg_soft_score - conflict_penalty))
        
        return fitness
    
    def update_timetable_metrics(self, timetable: Timetable):
        """
        Update timetable quality metrics after generation.
        
        Args:
            timetable: Timetable to update
        """
        # Calculate fitness
        fitness = self.calculate_fitness(timetable.id)
        
        # Count conflicts
        stmt = select(TimetableSlot).where(TimetableSlot.timetable_id == timetable.id)
        slot_count = len(list(self.db.execute(stmt).scalars().all()))
        
        # Detect conflicts for count
        conflicts = self.conflict_detector.detect_all_conflicts(self.db, timetable.id)
        
        timetable.quality_score = fitness
        timetable.conflict_count = len(conflicts)
        timetable.status = "completed" if len(conflicts) == 0 else "completed"
        
        self.db.commit()
    
    @staticmethod
    def rank_solutions(solutions: list[Timetable]) -> list[Timetable]:
        """
        Rank solutions by quality (lower conflicts, higher quality).
        
        Args:
            solutions: List of Timetable objects
            
        Returns:
            Sorted list (best first)
        """
        return sorted(
            solutions,
            key=lambda t: (t.conflict_count, -t.quality_score)
        )
    
    def get_all_resources(self, semester_id: int) -> dict:
        """
        Fetch all resources needed for generation.
        
        Args:
            semester_id: Semester ID
            
        Returns:
            Dict with sections, rooms, time_slots, etc.
        """
        semester = self.db.get(Semester, semester_id)
        
        # Get all sections (across all departments)
        sections = list(self.db.execute(select(Section)).scalars().all())
        
        # Get all rooms
        rooms = list(self.db.execute(select(Room)).scalars().all())
        
        # Get all time slots
        time_slots = list(self.db.execute(select(TimeSlot)).scalars().all())
        
        return {
            "semester": semester,
            "sections": sections,
            "rooms": rooms,
            "time_slots": time_slots,
            "days": list(range(5))  # Monday-Friday (0-4)
        }
