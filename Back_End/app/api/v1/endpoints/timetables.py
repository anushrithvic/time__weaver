"""
Module: Timetable Generation API Endpoints (Module 3)
Repository: timeweaver_backend
Owner: Pranathi Nibhanipudi
Epic: 3 - Timetable Generation / Re-generation

REST API endpoints for timetable generation, viewing, and management.

Key Endpoints:
    POST /api/v1/timetables/generate - Generate new timetable
    GET  /api/v1/timetables - List all timetables with filters
    GET  /api/v1/timetables/{id} - Get specific timetable
    GET  /api/v1/timetables/{id}/slots - Get timetable slots
    GET  /api/v1/timetables/{id}/conflicts - Get conflicts
    GET  /api/v1/timetables/view - View timetable by section/year/dept
    DELETE /api/v1/timetables/{id} - Delete timetable

Dependencies:
    - app.services.ga_generator (GeneticAlgorithmGenerator)
    - app.services.conflict_detector (ConflictDetector)
    - app.models.timetable (Timetable, TimetableSlot, Conflict)

User Stories: 3.3.2 (Generation), 3.1.2 (Conflicts)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import joinedload
from typing import Optional
from datetime import datetime

from app.db.session import get_db
from app.models.user import User, UserRole
from app.core.dependencies import get_current_admin, get_current_user
from app.models.timetable import Timetable, TimetableSlot, Conflict
from app.models.semester import Semester
from app.models.section import Section
from app.models.course import Course
from app.models.room import Room
from app.services.ga_generator import GeneticAlgorithmGenerator
from app.services.conflict_detector import ConflictDetector
from app.schemas.timetable import (
    TimetableCreate,
    TimetableResponse,
    TimetableListResponse,
    TimetableSlotResponse,
    ConflictResponse,
    TimetableStatus
)

router = APIRouter()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_error_response(error: str, message: str, code: int):
    """Create structured error response"""
    return {
        "error": error,
        "message": message,
        "code": code
    }


# ============================================================================
# TIMETABLE GENERATION
# ============================================================================

@router.post("/generate", response_model=TimetableResponse, status_code=status.HTTP_201_CREATED)
async def generate_timetable(
    request: TimetableCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Generate a new timetable using Genetic Algorithm.
    
    **Epic 3: User Story 3.3.2** - Timetable Generation
    **Permissions:** Admin only
    
    Args:
        request: Generation parameters (semester_id, num_solutions, etc.)
        db: Database session
        current_admin: Current admin user
        
    Returns:
        TimetableResponse: Generated timetable metadata
        
    Raises:
        404: Semester not found
        400: Generation failed
        
    Example:
        ```
        POST /api/v1/timetables/generate
        {
            "semester_id": 1,
            "num_solutions": 5
        }
        ```
    """
    # Validate semester exists
    semester_query = select(Semester).where(Semester.id == request.semester_id)
    semester_result = await db.execute(semester_query)
    semester = semester_result.scalar_one_or_none()
    
    if not semester:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                "NOT_FOUND",
                f"Semester with id {request.semester_id} not found",
                404
            )
        )
    
    try:
        # Initialize GA generator with optimized defaults
        generator = GeneticAlgorithmGenerator(
            db=db,
            population_size=50,  # Optimized default
            max_generations=100  # Optimized default
        )
        
        # Generate timetable
        start_time = datetime.now()
        solutions = await generator.generate(
            semester_id=request.semester_id,
            num_solutions=request.num_solutions
        )
        end_time = datetime.now()
        generation_time = (end_time - start_time).total_seconds()
        
        if not solutions:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=create_error_response(
                    "GENERATION_FAILED",
                    "Failed to generate any valid timetable solutions",
                    500
                )
            )
        
        # Get best solution
        best_solution = solutions[0]
        
        # Update metadata
        best_solution.generation_algorithm = "GA"  # Always use Genetic Algorithm
        best_solution.generation_time_seconds = generation_time
        best_solution.created_by_user_id = current_admin.id
        best_solution.status = TimetableStatus.COMPLETED
        
        await db.commit()
        await db.refresh(best_solution)
        
        return best_solution
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                "GENERATION_ERROR",
                f"Error during generation: {str(e)}",
                500
            )
        )


# ============================================================================
# TIMETABLE LISTING & VIEWING
# ============================================================================

@router.get("/", response_model=TimetableListResponse)
async def list_timetables(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    semester_id: Optional[int] = Query(None, description="Filter by semester ID"),
    status: Optional[TimetableStatus] = Query(None, description="Filter by status"),
    is_published: Optional[bool] = Query(None, description="Filter by publication status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all timetables with optional filters.
    
    Supports filtering by semester, status, and publication status.
    Includes pagination.
    
    **Permissions:** All authenticated users
    
    Args:
        skip: Pagination offset
        limit: Max results
        semester_id: Filter by semester
        status: Filter by generation status
        is_published: Filter by publication status
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        TimetableListResponse: List of timetables with total count
        
    Example:
        ```
        GET /api/v1/timetables?semester_id=1&status=COMPLETED&skip=0&limit=20
        ```
    """
    query = select(Timetable)
    
    # Apply filters
    if semester_id:
        query = query.where(Timetable.semester_id == semester_id)
    if status:
        query = query.where(Timetable.status == status)
    if is_published is not None:
        query = query.where(Timetable.is_published == is_published)
    
    # Order by creation date (newest first)
    query = query.order_by(Timetable.created_at.desc())
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    timetables = result.scalars().all()
    
    # Get total count
    count_query = select(func.count()).select_from(Timetable)
    if semester_id:
        count_query = count_query.where(Timetable.semester_id == semester_id)
    if status:
        count_query = count_query.where(Timetable.status == status)
    if is_published is not None:
        count_query = count_query.where(Timetable.is_published == is_published)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    return TimetableListResponse(
        data=timetables,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit
    )


@router.get("/view")
async def view_timetable(
    department_id: Optional[int] = Query(None, description="Department ID"),
    year_level: Optional[int] = Query(None, ge=1, le=4, description="Year level (1-4)"),
    section_name: Optional[str] = Query(None, description="Section name (e.g., 'A', 'B')"),
    semester_id: int = Query(..., description="Semester ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    View timetable for specific department/year/section.
    
    Allows students and faculty to view their section's timetable.
    Admin can view any timetable.
    
    **Permissions:** All authenticated users
    
    Args:
        department_id: Department to filter by
        year_level: Year (1st/2nd/3rd/4th)
        section_name: Section name
        semester_id: Semester ID
        db: Database session
        current_user: Current user
        
    Returns:
        Timetable with slots for matching sections
        
    Example:
        ```
        GET /api/v1/timetables/view?department_id=1&year_level=3&section_name=A&semester_id=5
        ```
    """
    # Find published timetable for semester
    timetable_query = select(Timetable).where(
        Timetable.semester_id == semester_id,
        Timetable.is_published == True,
        Timetable.status == TimetableStatus.COMPLETED
    ).order_by(Timetable.created_at.desc())
    
    timetable_result = await db.execute(timetable_query)
    timetable = timetable_result.scalar_one_or_none()
    
    if not timetable:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                "NOT_FOUND",
                f"No published timetable found for semester {semester_id}",
                404
            )
        )
    
    # Build section filter
    section_query = select(Section)
    filters = []
    
    if department_id:
        filters.append(Section.department_id == department_id)
    if year_level:
        filters.append(Section.year_level == year_level)
    if section_name:
        filters.append(Section.section_name == section_name)
    
    if filters:
        section_query = section_query.where(and_(*filters))
    
    section_result = await db.execute(section_query)
    sections = section_result.scalars().all()
    
    if not sections:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                "NOT_FOUND",
                "No sections found matching filters",
                404
            )
        )
    
    section_ids = [s.id for s in sections]
    
    # Get slots for these sections
    slots_query = select(TimetableSlot).where(
        TimetableSlot.timetable_id == timetable.id,
        TimetableSlot.section_id.in_(section_ids)
    ).options(
        joinedload(TimetableSlot.section),
        joinedload(TimetableSlot.course),
        joinedload(TimetableSlot.room)
    ).order_by(
        TimetableSlot.day_of_week,
        TimetableSlot.start_slot_id
    )
    
    slots_result = await db.execute(slots_query)
    slots = slots_result.scalars().all()
    
    return {
        "timetable": timetable,
        "sections": sections,
        "slots": slots,
        "total_slots": len(slots)
    }


@router.get("/{timetable_id}", response_model=TimetableResponse)
async def get_timetable(
    timetable_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific timetable by ID.
    
    **Permissions:** All authenticated users
    
    Args:
        timetable_id: Timetable ID
        db: Database session
        current_user: Current user
        
    Returns:
        TimetableResponse: Timetable metadata
        
    Raises:
        404: Timetable not found
        
    Example:
        ```
        GET /api/v1/timetables/123
        ```
    """
    query = select(Timetable).where(Timetable.id == timetable_id)
    result = await db.execute(query)
    timetable = result.scalar_one_or_none()
    
    if not timetable:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                "NOT_FOUND",
                f"Timetable with id {timetable_id} not found",
                404
            )
        )
    
    return timetable


# ============================================================================
# TIMETABLE SLOTS & CONFLICTS
# ============================================================================

@router.get("/{timetable_id}/slots")
async def get_timetable_slots(
    timetable_id: int,
    section_id: Optional[int] = Query(None, description="Filter by section"),
    day_of_week: Optional[int] = Query(None, ge=0, le=6, description="Filter by day (0-6)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all slots for a timetable with optional filters.
    
    Includes denormalized section/course/room data for display.
    
    **Permissions:** All authenticated users
    
    Args:
        timetable_id: Timetable ID
        section_id: Filter by section
        day_of_week: Filter by day
        db: Database session
        current_user: Current user
        
    Returns:
        List of timetable slots with joined data
        
    Example:
        ```
        GET /api/v1/timetables/123/slots?section_id=5&day_of_week=1
        ```
    """
    # Verify timetable exists
    tt_query = select(Timetable).where(Timetable.id == timetable_id)
    tt_result = await db.execute(tt_query)
    timetable = tt_result.scalar_one_or_none()
    
    if not timetable:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                "NOT_FOUND",
                f"Timetable with id {timetable_id} not found",
                404
            )
        )
    
    # Build query with filters
    query = select(TimetableSlot).where(
        TimetableSlot.timetable_id == timetable_id
    ).options(
        joinedload(TimetableSlot.section),
        joinedload(TimetableSlot.course),
        joinedload(TimetableSlot.room)
    )
    
    if section_id:
        query = query.where(TimetableSlot.section_id == section_id)
    if day_of_week is not None:
        query = query.where(TimetableSlot.day_of_week == day_of_week)
    
    query = query.order_by(
        TimetableSlot.day_of_week,
        TimetableSlot.start_slot_id
    )
    
    result = await db.execute(query)
    slots = result.scalars().all()
    
    return {
        "timetable_id": timetable_id,
        "slots": slots,
        "total": len(slots)
    }


@router.get("/{timetable_id}/conflicts", response_model=list[ConflictResponse])
async def get_timetable_conflicts(
    timetable_id: int,
    severity: Optional[str] = Query(None, description="Filter by severity"),
    is_resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all conflicts for a timetable.
    
    **Epic 3: User Story 3.1.2** - Conflict Detection
    **Permissions:** All authenticated users
    
    Args:
        timetable_id: Timetable ID
        severity: Filter by severity level
        is_resolved: Filter by resolution status
        db: Database session
        current_user: Current user
        
    Returns:
        List of conflicts
        
    Example:
        ```
        GET /api/v1/timetables/123/conflicts?severity=HIGH&is_resolved=false
        ```
    """
    # Verify timetable exists
    tt_query = select(Timetable).where(Timetable.id == timetable_id)
    tt_result = await db.execute(tt_query)
    timetable = tt_result.scalar_one_or_none()
    
    if not timetable:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                "NOT_FOUND",
                f"Timetable with id {timetable_id} not found",
                404
            )
        )
    
    # Build query
    query = select(Conflict).where(Conflict.timetable_id == timetable_id)
    
    if severity:
        query = query.where(Conflict.severity == severity)
    if is_resolved is not None:
        query = query.where(Conflict.is_resolved == is_resolved)
    
    query = query.order_by(Conflict.severity.desc(), Conflict.detected_at.desc())
    
    result = await db.execute(query)
    conflicts = result.scalars().all()
    
    return conflicts


# ============================================================================
# TIMETABLE MANAGEMENT
# ============================================================================

@router.delete("/{timetable_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timetable(
    timetable_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Delete a timetable and all its slots.
    
    **Permissions:** Admin only
    
    Args:
        timetable_id: Timetable ID
        db: Database session
        current_admin: Current admin user
        
    Raises:
        404: Timetable not found
        400: Cannot delete published timetable
        
    Example:
        ```
        DELETE /api/v1/timetables/123
        ```
    """
    query = select(Timetable).where(Timetable.id == timetable_id)
    result = await db.execute(query)
    timetable = result.scalar_one_or_none()
    
    if not timetable:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                "NOT_FOUND",
                f"Timetable with id {timetable_id} not found",
                404
            )
        )
    
    if timetable.is_published:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                "CANNOT_DELETE_PUBLISHED",
                "Cannot delete a published timetable. Unpublish it first.",
                400
            )
        )
    
    await db.delete(timetable)
    await db.commit()
    
    return None
