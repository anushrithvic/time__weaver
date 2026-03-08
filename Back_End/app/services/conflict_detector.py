"""
Module: Timetable Generation & Scheduling (Module 3)
Repository: timeweaver_backend
Owner: Pranathi Nibhanipudi
Epic: 3 - Timetable Generation / Re-generation

Conflict Detection Service - User Story 3.1

Detects scheduling conflicts in generated timetables:
- Room clashes (same room, time, day)
- Faculty clashes (same faculty, time, day)
- Student clashes (same section/elective, time, day)
- Capacity violations
- Lab requirement violations

Creates Conflict records with severity levels for resolution tracking.

Dependencies:
    - app.models.timetable (Timetable, TimetableSlot, Conflict)
    - app.models.room (Room model)
    - app.models.section (Section model)
    - app.models.course (Course model)

User Stories: 3.1.2 (Conflict Detection)
"""

from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from collections import defaultdict
from datetime import datetime
from app.models.timetable import Timetable, TimetableSlot, Conflict
from app.models.room import Room
from app.models.section import Section
from app.models.course import Course


class ConflictDetector:
    """Service for detecting scheduling conflicts"""
    
    @staticmethod
    def detect_room_conflicts(db: Session, timetable_id: int) -> list[Conflict]:
        """
        Detect ROOM_CLASH conflicts: same room booked multiple times.
        
        Args:
            db: Database session
            timetable_id: Timetable to check
            
        Returns:
            List of Conflict records
        """
        # Get all slots for this timetable
        stmt = select(TimetableSlot).where(TimetableSlot.timetable_id == timetable_id)
        slots = list(db.execute(stmt).scalars().all())
        
        conflicts = []
        
        # Group slots by (room_id, day_of_week, start_slot_id)
        room_schedule = defaultdict(list)
        for slot in slots:
            # For multi-slot courses, check each occupied slot
            for occupied_slot_offset in range(slot.duration_slots):
                key = (slot.room_id, slot.day_of_week, slot.start_slot_id + occupied_slot_offset)
                room_schedule[key].append(slot)
        
        # Find conflicts
        for (room_id, day, time_slot), conflicting_slots in room_schedule.items():
            if len(conflicting_slots) > 1:
                conflict = Conflict(
                    timetable_id=timetable_id,
                    conflict_type="ROOM_CLASH",
                    severity="HIGH",
                    slot_ids=[s.id for s in conflicting_slots],
                    description=f"Room {room_id} double-booked on day {day} slot {time_slot}",
                    is_resolved=False
                )
                conflicts.append(conflict)
        
        return conflicts
    
    @staticmethod
    def detect_faculty_conflicts(db: Session, timetable_id: int) -> list[Conflict]:
        """
        Detect FACULTY_CLASH conflicts: faculty teaching multiple classes simultaneously.
        
        Args:
            db: Database session
            timetable_id: Timetable to check
            
        Returns:
            List of Conflict records
        """
        stmt = select(TimetableSlot).where(TimetableSlot.timetable_id == timetable_id)
        slots = list(db.execute(stmt).scalars().all())
        
        conflicts = []
        
        # Group slots by (faculty_id, day_of_week, start_slot_id)
        faculty_schedule = defaultdict(list)
        for slot in slots:
            if not slot.primary_faculty_id:
                continue
            
            # Check each occupied slot for multi-slot courses
            for occupied_slot_offset in range(slot.duration_slots):
                key = (slot.primary_faculty_id, slot.day_of_week, slot.start_slot_id + occupied_slot_offset)
                faculty_schedule[key].append(slot)
        
        # Find conflicts
        for (faculty_id, day, time_slot), conflicting_slots in faculty_schedule.items():
            if len(conflicting_slots) > 1:
                conflict = Conflict(
                    timetable_id=timetable_id,
                    conflict_type="FACULTY_CLASH",
                    severity="HIGH",
                    slot_ids=[s.id for s in conflicting_slots],
                    description=f"Faculty {faculty_id} assigned to {len(conflicting_slots)} classes on day {day} slot {time_slot}",
                    is_resolved=False
                )
                conflicts.append(conflict)
        
        return conflicts
    
    @staticmethod
    def detect_student_conflicts(db: Session, timetable_id: int) -> list[Conflict]:
        """
        Detect STUDENT_CLASH conflicts: section has multiple classes at same time.
        
        Args:
            db: Database session
            timetable_id: Timetable to check
            
        Returns:
            List of Conflict records
        """
        stmt = select(TimetableSlot).where(TimetableSlot.timetable_id == timetable_id)
        slots = list(db.execute(stmt).scalars().all())
        
        conflicts = []
        
        # Group slots by (section_id, day_of_week, start_slot_id)
        section_schedule = defaultdict(list)
        for slot in slots:
            # Check each occupied slot for multi-slot courses
            for occupied_slot_offset in range(slot.duration_slots):
                key = (slot.section_id, slot.day_of_week, slot.start_slot_id + occupied_slot_offset)
                section_schedule[key].append(slot)
        
        # Find conflicts
        for (section_id, day, time_slot), conflicting_slots in section_schedule.items():
            if len(conflicting_slots) > 1:
                conflict = Conflict(
                    timetable_id=timetable_id,
                    conflict_type="STUDENT_CLASH",
                    severity="HIGH",
                    slot_ids=[s.id for s in conflicting_slots],
                    description=f"Section {section_id} has {len(conflicting_slots)} classes on day {day} slot {time_slot}",
                    is_resolved=False
                )
                conflicts.append(conflict)
        
        return conflicts
    
    @staticmethod
    def detect_capacity_violations(db: Session, timetable_id: int) -> list[Conflict]:
        """
        Detect CAPACITY_VIOLATION conflicts: room too small for section.
        
        Args:
            db: Database session
            timetable_id: Timetable to check
            
        Returns:
            List of Conflict records
        """
        stmt = (
            select(TimetableSlot, Room, Section)
            .join(Room, TimetableSlot.room_id == Room.id)
            .join(Section, TimetableSlot.section_id == Section.id)
            .where(TimetableSlot.timetable_id == timetable_id)
        )
        
        result = db.execute(stmt)
        conflicts = []
        
        for slot, room, section in result:
            if room.capacity < section.student_count:
                conflict = Conflict(
                    timetable_id=timetable_id,
                    conflict_type="CAPACITY_VIOLATION",
                    severity="HIGH",
                    slot_ids=[slot.id],
                    description=f"Room {room.full_name} (capacity {room.capacity}) assigned to section {section.name} ({section.student_count} students)",
                    is_resolved=False
                )
                conflicts.append(conflict)
        
        return conflicts
    
    @staticmethod
    def detect_lab_requirement_violations(db: Session, timetable_id: int) -> list[Conflict]:
        """
        Detect LAB_REQUIREMENT_VIOLATION: lab course in non-lab room.
        
        Args:
            db: Database session
            timetable_id: Timetable to check
            
        Returns:
            List of Conflict records
        """
        stmt = (
            select(TimetableSlot, Room, Course)
            .join(Room, TimetableSlot.room_id == Room.id)
            .join(Course, TimetableSlot.course_id == Course.id)
            .where(
                TimetableSlot.timetable_id == timetable_id,
                Course.requires_lab == True
            )
        )
        
        result = db.execute(stmt)
        conflicts = []
        
        for slot, room, course in result:
            if room.room_type != 'lab' or not room.has_lab_equipment:
                conflict = Conflict(
                    timetable_id=timetable_id,
                    conflict_type="LAB_REQUIREMENT_VIOLATION",
                    severity="MEDIUM",
                    slot_ids=[slot.id],
                    description=f"Lab course {course.code} assigned to non-lab room {room.full_name}",
                    is_resolved=False
                )
                conflicts.append(conflict)
        
        return conflicts
    
    @staticmethod
    def detect_all_conflicts(db: Session, timetable_id: int) -> list[Conflict]:
        """
        Run all conflict detection checks and return combined results.
        
        Args:
            db: Database session
            timetable_id: Timetable to check
            
        Returns:
            List of all Conflict records
        """
        all_conflicts = []
        
        all_conflicts.extend(ConflictDetector.detect_room_conflicts(db, timetable_id))
        all_conflicts.extend(ConflictDetector.detect_faculty_conflicts(db, timetable_id))
        all_conflicts.extend(ConflictDetector.detect_student_conflicts(db, timetable_id))
        all_conflicts.extend(ConflictDetector.detect_capacity_violations(db, timetable_id))
        all_conflicts.extend(ConflictDetector.detect_lab_requirement_violations(db, timetable_id))
        
        # Persist conflicts to database
        if all_conflicts:
            db.add_all(all_conflicts)
            db.commit()
        
        return all_conflicts
    
    @staticmethod
    def get_conflict_summary(db: Session, timetable_id: int) -> dict[str, any]:
        """
        Get conflict summary statistics for a timetable.
        
        Args:
            db: Database session
            timetable_id: Timetable to analyze
            
        Returns:
            Dict with conflict counts by type and severity
        """
        stmt = select(Conflict).where(Conflict.timetable_id == timetable_id)
        conflicts = list(db.execute(stmt).scalars().all())
        
        by_type = defaultdict(int)
        by_severity = defaultdict(int)
        
        for conflict in conflicts:
            by_type[conflict.conflict_type] += 1
            by_severity[conflict.severity] += 1
        
        return {
            "total_conflicts": len(conflicts),
            "by_type": dict(by_type),
            "by_severity": dict(by_severity),
            "unresolved_count": sum(1 for c in conflicts if not c.is_resolved)
        }
