"""
Module: Timetable Schemas (Module 3)
Repository: timeweaver_backend
Owner: Student C
Epic: 3 - AI/Backend Optimization & Conflict Detection

Pydantic schemas for request validation and response serialization
for timetable generation endpoints.

Dependencies:
    - app.models.timetable (Timetable, TimetableSlot, Conflict models)

Test Coverage: tests/test_schemas/test_timetable_schemas.py
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class GenerationAlgorithm(str, Enum):
    """Supported timetable generation algorithms"""
    GA = "GA"  # Genetic Algorithm
    SA = "SA"  # Simulated Annealing
    HYBRID = "HYBRID"  # GA + SA hybrid
    CSP_GREEDY = "CSP_GREEDY"  # CSP with greedy heuristic


class TimetableStatus(str, Enum):
    """Timetable generation status"""
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class ConflictType(str, Enum):
    """Types of scheduling conflicts"""
    ROOM_CLASH = "ROOM_CLASH"
    FACULTY_CLASH = "FACULTY_CLASH"
    STUDENT_CLASH = "STUDENT_CLASH"
    CAPACITY_VIOLATION = "CAPACITY_VIOLATION"
    LAB_REQUIREMENT_VIOLATION = "LAB_REQUIREMENT_VIOLATION"
    ELECTIVE_CLASH = "ELECTIVE_CLASH"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"


class ConflictSeverity(str, Enum):
    """Conflict severity levels"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class TimetableCreate(BaseModel):
    """
    Request schema for creating a new timetable.
    
    Used by: POST /api/v1/timetables/generate
    
    Attributes:
        semester_id: ID of semester to generate timetable for
        num_solutions: Number of alternative solutions to generate (default: 5)
    
    Note: The system uses optimized internal parameters for best results.
    
    Example:
        >>> request = TimetableCreate(semester_id=1, num_solutions=3)
    """
    semester_id: int = Field(..., gt=0, description="Semester ID to generate timetable for")
    num_solutions: int = Field(default=5, ge=1, le=10, description="Number of solutions to generate")


class SlotLockRequest(BaseModel):
    """
    Request schema for locking/unlocking slots.
    
    Used by: POST /api/v1/timetables/{id}/slots/lock
             POST /api/v1/timetables/{id}/slots/unlock
    
    Attributes:
        slot_ids: List of slot IDs to lock/unlock
    
    Example:
        >>> request = SlotLockRequest(slot_ids=[1, 2, 3, 4])
    """
    slot_ids: List[int] = Field(..., min_items=1, description="Slot IDs to lock/unlock")


class FacultyLeaveRequest(BaseModel):
    """
    Request schema for handling faculty leave.
    
    Used by: POST /api/v1/timetables/{id}/faculty-leave
    
    Triggers incremental re-optimization for affected slots.
    
    Attributes:
        faculty_id: Faculty member ID
        start_date: Leave start date
        end_date: Leave end date
    
    Example:
        >>> request = FacultyLeaveRequest(
        ...     faculty_id=10,
        ...     start_date=datetime(2024, 10, 1),
        ...     end_date=datetime(2024, 10, 7)
        ... )
    """
    faculty_id: int = Field(..., gt=0, description="Faculty member ID")
    start_date: datetime = Field(..., description="Leave start date")
    end_date: datetime = Field(..., description="Leave end date")
    
    @validator('end_date')
    def end_after_start(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class AddSectionRequest(BaseModel):
    """
    Request schema for adding new section to existing timetable.
    
    Used by: POST /api/v1/timetables/{id}/add-section
    
    Triggers local optimization to insert section with minimal impact.
    
    Attributes:
        section_id: Section ID to add
    
    Example:
    >>> request = AddSectionRequest(section_id=42)
    """
    section_id: int = Field(..., gt=0, description="Section ID to add")


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class TimetableSlotResponse(BaseModel):
    """
    Response schema for timetable slot with joined data.
    
    Used by: GET /api/v1/timetables/{id}/slots
    
    Includes denormalized data for frontend display.
    
    Attributes:
        id: Slot ID
        timetable_id: Parent timetable ID
        section_id: Section ID
        section_name: Section name (e.g., "CSE-A")
        course_code: Course code (e.g., "CS101")
        course_title: Course title (e.g., "Intro to CS")
        room_id: Room ID
        room_number: Room number (e.g., "201")
        time_slot_id: Time slot ID
        time_slot: Time range (e.g., "09:00 - 10:00")
        faculty_id: Faculty ID (nullable)
        faculty_name: Faculty name (nullable)
        day_of_week: Day (0-6)
        is_locked: Whether slot is locked
        created_at: Creation timestamp
    
    Example:
        >>> slot = TimetableSlotResponse(
        ...     id=1,
        ...     section_name="CSE-A",
        ...     course_code="CS101",
        ...     room_number="201",
        ...     time_slot="09:00 - 10:00",
        ...     day_of_week=0
        ... )
    """
    id: int
    timetable_id: int
    section_id: int
    section_name: str
    course_code: Optional[str]
    course_title: Optional[str]
    room_id: int
    room_number: str
    start_slot_id: int = Field(..., description="Starting time slot ID")
    duration_slots: int = Field(..., ge=1, le=5, description="Number of consecutive slots (1-5)")
    time_slot: str = Field(..., description="Human-readable time range")
    primary_faculty_id: Optional[int] = Field(None, description="Main instructor")
    faculty_name: Optional[str] = None
    assisting_faculty_ids: Optional[list[int]] = Field(default=[], description="Assisting faculty for labs")
    batch_number: Optional[int] = Field(None, description="Lab batch number (1-10)")
    day_of_week: int
    is_locked: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TimetableResponse(BaseModel):
    """
    Response schema for timetable metadata.
    
    Used by: GET /api/v1/timetables
             GET /api/v1/timetables/{id}
             POST /api/v1/timetables/generate
    
    Attributes:
        id: Timetable ID
        semester_id: Semester ID
        name: Timetable name
        status: Generation status
        quality_score: Fitness score (0.0-1.0)
        conflict_count: Number of conflicts
        is_published: Publication status
        generation_algorithm: Algorithm used
        generation_time_seconds: Generation time
        created_by_user_id: Creator user ID
        created_at: Creation timestamp
        updated_at: Last update timestamp
        published_at: Publication timestamp
    
    Example:
        >>> timetable = TimetableResponse(
        ...     id=1,
        ...     name="Fall 2024 - GA v1",
        ...     status=TimetableStatus.COMPLETED,
        ...     quality_score=0.92,
        ...     conflict_count=0
        ... )
    """
    id: int
    semester_id: int
    name: str
    status: TimetableStatus
    quality_score: Optional[float]
    conflict_count: int
    is_published: bool
    generation_algorithm: Optional[GenerationAlgorithm]
    generation_time_seconds: Optional[float]
    created_by_user_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ConflictResponse(BaseModel):
    """
    Response schema for detected conflicts.
    
    Used by: POST /api/v1/timetables/{id}/detect-conflicts
             GET /api/v1/timetables/{id}/conflicts
    
    Attributes:
        id: Conflict ID
        timetable_id: Parent timetable ID
        conflict_type: Type of conflict
        severity: Severity level
        slot_ids: List of conflicting slot IDs
        description: Human-readable description
        is_resolved: Resolution status
        resolution_notes: Resolution notes (if resolved)
        detected_at: Detection timestamp
        resolved_at: Resolution timestamp
    
    Example:
        >>> conflict = ConflictResponse(
        ...     id=1,
        ...     conflict_type=ConflictType.ROOM_CLASH,
        ...     severity=ConflictSeverity.HIGH,
        ...     slot_ids=[101, 102],
        ...     description="Room 201: CSE-A and ECE-B at Monday 9:00"
        ... )
    """
    id: int
    timetable_id: int
    conflict_type: ConflictType
    severity: ConflictSeverity
    slot_ids: List[int]
    description: str
    is_resolved: bool
    resolution_notes: Optional[str]
    detected_at: datetime
    resolved_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class GenerationStatusResponse(BaseModel):
    """
    Response schema for timetable generation job status.
    
    Used by: GET /api/v1/timetables/generation-status/{job_id}
    
    For async generation jobs using Celery.
    
    Attributes:
        job_id: Celery task ID
        status: Job status (PENDING, PROGRESS, SUCCESS, FAILURE)
        progress_percent: Generation progress (0-100)
        current_generation: Current GA generation number
        total_generations: Total generations to run
        message: Status message
        result: Timetable ID (when complete)
    
    Example:
        >>> status = GenerationStatusResponse(
        ...     job_id="abc-123",
        ...     status="PROGRESS",
        ...     progress_percent=45,
        ...     current_generation=45,
        ...     total_generations=100
        ... )
    """
    job_id: str
    status: str  # PENDING, PROGRESS, SUCCESS, FAILURE
    progress_percent: Optional[int] = None
    current_generation: Optional[int] = None
    total_generations: Optional[int] = None
    message: Optional[str] = None
    result: Optional[int] = None  # Timetable ID when complete
    
    @validator('progress_percent')
    def validate_progress(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('progress_percent must be between 0 and 100')
        return v


class TimetableListResponse(BaseModel):
    """
    Response schema for list of timetables.
    
    Used by: GET /api/v1/timetables
    
    Attributes:
        data: List of timetables
        total: Total count
        page: Current page
        page_size: Items per page
    
    Example:
        >>> response = TimetableListResponse(
        ...     data=[timetable1, timetable2],
        ...     total=2,
        ...     page=1,
        ...     page_size=10
        ... )
    """
    data: List[TimetableResponse]
    total: int
    page: int = 1
    page_size: int = 10
