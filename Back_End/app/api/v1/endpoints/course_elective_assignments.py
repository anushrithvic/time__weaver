"""
Module: Course Elective Assignment API Endpoints
Repository: timeweaver_backend
Epic: 1 - Academic Setup

REST API endpoints for assigning courses to elective groups per semester.

Key Endpoints:
    POST   /api/v1/course-elective-assignments - Create assignment
    GET    /api/v1/course-elective-assignments - List assignments with filters
    GET    /api/v1/course-elective-assignments/{id} - Get specific assignment
    PUT    /api/v1/course-elective-assignments/{id} - Update assignment
    DELETE /api/v1/course-elective-assignments/{id} - Delete assignment

Dependencies:
    - app.models.curriculum (CourseElectiveAssignment)
    - app.schemas.curriculum (CourseElectiveAssignmentCreate, CourseElectiveAssignmentUpdate, etc.)

User Stories: 1.5.2 (Elective Course Assignment)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional

from app.db.session import get_db
from app.models.user import User
from app.core.dependencies import get_current_admin
from app.models.curriculum import CourseElectiveAssignment
from app.schemas.curriculum import (
    CourseElectiveAssignmentCreate,
    CourseElectiveAssignmentUpdate,
    CourseElectiveAssignmentResponse,
    CourseElectiveAssignmentListResponse
)

router = APIRouter()


@router.post("/", response_model=CourseElectiveAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_course_elective_assignment(
    assignment_in: CourseElectiveAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Create a new course-elective group assignment.

    Associates a course with an elective group for a specific semester.
    Optionally pre-assigns a room for PE (Professional Elective) courses.

    **Epic 1: User Story 1.5.2** - Elective Course Assignment
    **Permissions:** Admin only

    Args:
        assignment_in: Assignment data (elective_group_id, semester_id, course_id, assigned_room_id)
        db: Database session
        current_admin: Current admin user

    Returns:
        CourseElectiveAssignmentResponse: Created assignment

    Raises:
        400: Assignment for this group/semester/course already exists
    """
    # Check for duplicate (group, semester, course) combination
    query = select(CourseElectiveAssignment).where(
        and_(
            CourseElectiveAssignment.elective_group_id == assignment_in.elective_group_id,
            CourseElectiveAssignment.course_id == assignment_in.course_id
        )
    )
    if assignment_in.semester_id is not None:
        query = query.where(CourseElectiveAssignment.semester_id == assignment_in.semester_id)
        
    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Course {assignment_in.course_id} is already assigned to elective group "
                   f"{assignment_in.elective_group_id} for semester {assignment_in.semester_id}"
        )

    assignment = CourseElectiveAssignment(**assignment_in.model_dump())
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)

    return assignment


@router.get("/", response_model=CourseElectiveAssignmentListResponse)
async def list_course_elective_assignments(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    elective_group_id: Optional[int] = Query(None, description="Filter by elective group ID"),
    semester_id: Optional[int] = Query(None, description="Filter by semester ID"),
    course_id: Optional[int] = Query(None, description="Filter by course ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of all course-elective assignments with optional filters.

    Supports filtering by elective group, semester, and course.
    Includes pagination.

    Args:
        skip: Pagination offset
        limit: Max results
        elective_group_id: Filter by elective group
        semester_id: Filter by semester
        course_id: Filter by course
        db: Database session

    Returns:
        CourseElectiveAssignmentListResponse: List of assignments with total count
    """
    query = select(CourseElectiveAssignment)

    # Apply filters
    if elective_group_id:
        query = query.where(CourseElectiveAssignment.elective_group_id == elective_group_id)
    if semester_id:
        if semester_id:
            query = query.where(CourseElectiveAssignment.semester_id == semester_id)
    if course_id:
        query = query.where(CourseElectiveAssignment.course_id == course_id)

    # Order and paginate
    query = query.order_by(
        CourseElectiveAssignment.elective_group_id,
        CourseElectiveAssignment.semester_id,
        CourseElectiveAssignment.course_id
    ).offset(skip).limit(limit)

    result = await db.execute(query)
    assignments = result.scalars().all()

    # Get total count
    count_query = select(func.count()).select_from(CourseElectiveAssignment)
    if elective_group_id:
        count_query = count_query.where(CourseElectiveAssignment.elective_group_id == elective_group_id)
    if semester_id:
        if semester_id:
            count_query = count_query.where(CourseElectiveAssignment.semester_id == semester_id)
    if course_id:
        count_query = count_query.where(CourseElectiveAssignment.course_id == course_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    return CourseElectiveAssignmentListResponse(data=assignments, total=total)


@router.get("/{assignment_id}", response_model=CourseElectiveAssignmentResponse)
async def get_course_elective_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific course-elective assignment by ID.

    Args:
        assignment_id: Assignment ID
        db: Database session

    Returns:
        CourseElectiveAssignmentResponse: Assignment details

    Raises:
        404: Assignment not found
    """
    query = select(CourseElectiveAssignment).where(CourseElectiveAssignment.id == assignment_id)
    result = await db.execute(query)
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course elective assignment with id {assignment_id} not found"
        )

    return assignment


@router.put("/{assignment_id}", response_model=CourseElectiveAssignmentResponse)
async def update_course_elective_assignment(
    assignment_id: int,
    assignment_update: CourseElectiveAssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Update a course-elective assignment (typically to change room assignment).

    **Permissions:** Admin only

    Args:
        assignment_id: Assignment ID
        assignment_update: Updated assignment data
        db: Database session
        current_admin: Current admin user

    Returns:
        CourseElectiveAssignmentResponse: Updated assignment

    Raises:
        404: Assignment not found
    """
    query = select(CourseElectiveAssignment).where(CourseElectiveAssignment.id == assignment_id)
    result = await db.execute(query)
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course elective assignment with id {assignment_id} not found"
        )

    update_data = assignment_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assignment, field, value)

    await db.commit()
    await db.refresh(assignment)

    return assignment


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course_elective_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Delete a course-elective assignment.

    **Permissions:** Admin only

    Args:
        assignment_id: Assignment ID
        db: Database session
        current_admin: Current admin user

    Raises:
        404: Assignment not found
    """
    query = select(CourseElectiveAssignment).where(CourseElectiveAssignment.id == assignment_id)
    result = await db.execute(query)
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course elective assignment with id {assignment_id} not found"
        )

    await db.delete(assignment)
    await db.commit()

    return None
