"""
Module: Timetable Generation & Scheduling (Module 3)
Repository: timeweaver_backend
Owner: Pranathi Nibhanipudi
Epic: 3 - AI/Backend Optimization & Conflict Detection

This module defines the database models for AI-generated timetables.
Supports CSP + Genetic Algorithm optimization with conflict detection,
slot locking, and incremental re-optimization.

Key Models:
    - Timetable: Generated schedule metadata with quality metrics
    - TimetableSlot: Individual class session assignments
    - Conflict: Detected scheduling conflicts

Dependencies:
    - app.models.section (Section model)
    - app.models.room (Room model)
    - app.models.time_slot (TimeSlot model)
    - app.models.semester (Semester model)

User Stories:
    - 3.1: Automatic conflict detection
    - 3.2: Slot locking for critical assignments
    - 3.3: Multiple timetable generation
    - 3.5: Multi-objective optimization with scoring
    - 3.6: Incremental updates for faculty leave
    - 3.8: Minimal change tracking

Test Coverage: tests/test_models/test_timetable_models.py
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Timetable(Base):
    """
    Generated timetable for a semester.
    
    Stores metadata about AI-generated schedules including quality scores,
    generation algorithm, and publication status. Multiple timetables can
    be generated for comparison (User Story 3.3).
    
    Attributes:
        id: Primary key
        semester_id: Foreign key to semesters table
        name: Human-readable name (e.g., "Fall 2024 - GA v1")
        status: Generation status (generating|completed|failed|archived)
        quality_score: Fitness score 0.0-1.0 from optimization
        conflict_count: Number of detected hard constraint violations
        is_published: Whether timetable is active/visible to users
        generation_algorithm: Algorithm used (GA|SA|HYBRID|CSP_GREEDY)
        generation_time_seconds: Time taken to generate
        generation_config: JSON config (population size, generations, etc.)
        created_by_user_id: Admin who triggered generation
        created_at: Generation timestamp
        updated_at: Last modification timestamp
        published_at: Publication timestamp
    
    Constraints:
        - status must be one of: generating, completed, failed, archived
        - quality_score must be between 0.0 and 1.0
        - conflict_count must be >= 0
        - generation_algorithm must be: GA, SA, HYBRID, or CSP_GREEDY
    
    Test Coverage: tests/test_models/test_timetable_models.py::test_timetable_creation
    
    Example:
        >>> timetable = Timetable(
        ...     semester_id=1,
        ...     name="Fall 2024 - GA v1",
        ...     status="completed",
        ...     quality_score=0.92,
        ...     generation_algorithm="GA"
        ... )
    """
    __tablename__ = "timetables"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Core Fields
    semester_id = Column(Integer, ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    
    # Generation Status
    status = Column(String(20), nullable=False, default="generating", index=True)
    
    # Quality Metrics (Epic 3 - User Story 3.5)
    quality_score = Column(Float, nullable=True)  # 0.0 to 1.0
    conflict_count = Column(Integer, default=0, nullable=False)
    
    # Publication Status
    is_published = Column(Boolean, default=False, nullable=False, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Generation Metadata
    generation_algorithm = Column(String(20), nullable=True)
    generation_time_seconds = Column(Float, nullable=True)
    generation_config = Column(Text, nullable=True)  # JSON string
    
    # Audit Fields
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Database Constraints
    __table_args__ = (
        CheckConstraint("status IN ('generating', 'completed', 'failed', 'archived')", name="check_status_valid"),
        CheckConstraint("quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)", name="check_quality_score_range"),
        CheckConstraint("conflict_count >= 0", name="check_conflict_count_positive"),
        CheckConstraint("generation_algorithm IS NULL OR generation_algorithm IN ('GA', 'SA', 'HYBRID', 'CSP_GREEDY')", name="check_algorithm_valid"),
    )
    
    def __repr__(self):
        return f"<Timetable(id={self.id}, name='{self.name}', status='{self.status}', quality={self.quality_score})>"


class TimetableSlot(Base):
    """
    Individual class session assignment in a timetable.
    
    Represents one scheduled class: assigns a section to a specific room,
    time slot(s), day, and faculty member(s). Supports multi-slot courses (CIR, labs)
    via duration_slots field, and lab batching via batch_number.
    Supports locking critical slots to prevent modification during re-optimization (User Story 3.2).
    
    Attributes:
        id: Primary key
        timetable_id: Parent timetable foreign key
        section_id: Section being scheduled
        course_id: Course (denormalized for performance)
        room_id: Assigned room
        start_slot_id: Starting time slot number (references time_slots.slot_number)
        duration_slots: Number of consecutive slots (1=regular class, 3=CIR/lab)
        day_of_week: Day (0=Monday, 6=Sunday)
        primary_faculty_id: Main faculty member assigned
        assisting_faculty_ids: Array of additional faculty (for labs requiring multiple instructors)
        batch_number: For lab batching (1, 2, ..., NULL for non-batched)
       is_locked: Protected from re-optimization (User Story 3.2)
        created_at: Assignment timestamp
    
    Constraints:
        - day_of_week must be between 0 and 6
        - duration_slots must be between 1 and 5
    
    Indexes:
        - Composite on (timetable_id, day, room_id) for conflict detection
        - Index on (primary_faculty_id, day) for faculty conflicts
    
    Test Coverage: tests/test_models/test_timetable_models.py::test_slot_creation
    
    Example:
        >>> # Regular 1-hour class
        >>> slot = TimetableSlot(
        ...     timetable_id=1,
        ...     section_id=10,
        ...     room_id=101,
        ...     start_slot_id=4,  # Slot 4
        ...     duration_slots=1,  # Occupies only slot 4
        ...     day_of_week=0,  # Monday
        ...     is_locked=False
        ... )
        >>> # CIR 3-hour block
        >>> cir_slot = TimetableSlot(
        ...     timetable_id=1,
        ...     section_id=10,
        ...     room_id=101,
        ...     start_slot_id=4,  # Slots 4, 5, 6
        ...     duration_slots=3,
        ...     day_of_week=0
        ... )
    """
    __tablename__ = "timetable_slots"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Parent Timetable
    timetable_id = Column(Integer, ForeignKey("timetables.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Assignment Fields
    section_id = Column(Integer, ForeignKey("sections.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, nullable=True)  # Will add FK later
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Multi-slot support (User Story 3.1, 3.3)
    start_slot_id = Column(Integer, ForeignKey("time_slots.id"), nullable=False, index=True)
    duration_slots = Column(Integer, nullable=False, default=1)  # 1=single slot, 3=CIR/3-hour lab
    
    # Scheduling Fields
    day_of_week = Column(Integer, nullable=False)  # 0-6 (Monday-Sunday)
    
    # Faculty Assignment
    primary_faculty_id = Column(Integer, nullable=True, index=True)  # Will add FK later
    assisting_faculty_ids = Column(ARRAY(Integer), default=list)  # For labs needing multiple faculty
    
    # Lab Batching (institutional config)
    batch_number = Column(Integer, nullable=True)  # 1, 2, ... (NULL for non-batched courses)
    
    # Slot Locking (Epic 3 - User Story 3.2)
    is_locked = Column(Boolean, default=False, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Database Constraints
    __table_args__ = (
        CheckConstraint("day_of_week >= 0 AND day_of_week <= 6", name="check_day_of_week_valid"),
        CheckConstraint("duration_slots >= 1 AND duration_slots <= 5", name="check_duration_slots_valid"),
        CheckConstraint("batch_number IS NULL OR batch_number > 0", name="check_batch_number_positive"),
    )
    
    def __repr__(self):
        return f"<TimetableSlot(id={self.id}, section={self.section_id}, room={self.room_id}, day={self.day_of_week}, slots={self.start_slot_id}+{self.duration_slots})>"


class Conflict(Base):
    """
    Detected scheduling conflict in a timetable.
    
    Tracks conflicts found by automatic conflict detector (User Story 3.1).
    Provides transparency and enables manual conflict resolution.
    
    Attributes:
        id: Primary key
        timetable_id: Parent timetable foreign key
        conflict_type: Type (ROOM_CLASH, FACULTY_CLASH, STUDENT_CLASH, etc.)
        severity: Severity level (HIGH|MEDIUM|LOW)
        slot_ids: Array of conflicting slot IDs
        description: Human-readable conflict explanation
        is_resolved: Whether manually resolved
        resolution_notes: Notes on resolution
        detected_at: Detection timestamp
        resolved_at: Resolution timestamp
    
    Conflict Types:
        - ROOM_CLASH: Room double-booked
        - FACULTY_CLASH: Faculty teaching multiple classes simultaneously
        - STUDENT_CLASH: Students have overlapping classes
        - CAPACITY_VIOLATION: Room too small for section
        - LAB_REQUIREMENT_VIOLATION: Lab course in non-lab room
        - ELECTIVE_CLASH: Elective group conflicts
        - CONSTRAINT_VIOLATION: Other constraint violations
    
    Test Coverage: tests/test_models/test_timetable_models.py::test_conflict_creation
    
    Example:
        >>> conflict = Conflict(
        ...     timetable_id=1,
        ...     conflict_type="ROOM_CLASH",
        ...     severity="HIGH",
        ...     slot_ids=[101, 102],
        ...     description="Room 201: CSE-A and ECE-B both at Monday 9:00 AM"
        ... )
    """
    __tablename__ = "conflicts"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Parent Timetable
    timetable_id = Column(Integer, ForeignKey("timetables.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Conflict Details
    conflict_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, default="HIGH")
    
    # Conflicting Slots
    slot_ids = Column(ARRAY(Integer), nullable=False)
    
    # Description
    description = Column(Text, nullable=False)
    
    # Resolution Tracking
    is_resolved = Column(Boolean, default=False, nullable=False, index=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Timestamps
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Database Constraints
    __table_args__ = (
        CheckConstraint(
            """conflict_type IN (
                'ROOM_CLASH', 'FACULTY_CLASH', 'STUDENT_CLASH',
                'CAPACITY_VIOLATION', 'LAB_REQUIREMENT_VIOLATION',
                'ELECTIVE_CLASH', 'CONSTRAINT_VIOLATION'
            )""",
            name="check_conflict_type_valid"
        ),
        CheckConstraint("severity IN ('HIGH', 'MEDIUM', 'LOW')", name="check_severity_valid"),
    )
    
    def __repr__(self):
        return f"<Conflict(id={self.id}, type='{self.conflict_type}', severity='{self.severity}', resolved={self.is_resolved})>"
