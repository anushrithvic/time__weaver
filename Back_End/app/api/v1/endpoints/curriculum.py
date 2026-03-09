"""
Module: Curriculum Management API Endpoints
Repository: timeweaver_backend
Epic: 1 - Academic Setup

REST API endpoints for curriculum management (mapping courses to department/year/semester_type).

Key Endpoints:
    POST   /api/v1/curriculum - Create curriculum entry
    GET    /api/v1/curriculum - List curriculum with filters
    GET    /api/v1/curriculum/{id} - Get specific curriculum entry
    PUT    /api/v1/curriculum/{id} - Update curriculum entry
    DELETE /api/v1/curriculum/{id} - Delete curriculum entry

Dependencies:
    - app.models.curriculum (Curriculum)
    - app.schemas.curriculum (CurriculumCreate, CurriculumUpdate, CurriculumResponse, CurriculumListResponse)

User Stories: 1.4.2 (Curriculum Management)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional

from app.db.session import get_db
from app.models.user import User
from app.core.dependencies import get_current_admin
from app.models.curriculum import Curriculum
from app.schemas.curriculum import (
    CurriculumCreate,
    CurriculumUpdate,
    CurriculumResponse,
    CurriculumListResponse
)

router = APIRouter()


@router.post("/", response_model=CurriculumResponse, status_code=status.HTTP_201_CREATED)
async def create_curriculum(
    curriculum_in: CurriculumCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Create a new curriculum entry mapping a course or elective group to department/year/semester_type.

    **Epic 1: User Story 1.4.2** - Curriculum Management
    **Permissions:** Admin only

    Args:
        curriculum_in: Curriculum data (department_id, year_level, semester_type, course_id, elective_group_id, is_mandatory)
        db: Database session
        current_admin: Current admin user

    Returns:
        CurriculumResponse: Created curriculum entry

    Raises:
        400: Duplicate curriculum entry already exists
    """
    # Check for duplicate combination exactly (allowing multiple courses for the same department/year/sem)
    conditions = [
        Curriculum.department_id == curriculum_in.department_id,
        Curriculum.year_level == curriculum_in.year_level,
        Curriculum.semester_type == curriculum_in.semester_type,
    ]
    
    if curriculum_in.course_id:
        conditions.append(Curriculum.course_id == curriculum_in.course_id)
    else:
        conditions.append(Curriculum.elective_group_id == curriculum_in.elective_group_id)

    query = select(Curriculum).where(and_(*conditions))
    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        entity_str = f"course {curriculum_in.course_id}" if curriculum_in.course_id else f"elective group {curriculum_in.elective_group_id}"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Curriculum entry for department {curriculum_in.department_id}, "
                   f"year {curriculum_in.year_level}, "
                   f"semester {curriculum_in.semester_type}, "
                   f"{entity_str} already exists"
        )

    curriculum = Curriculum(**curriculum_in.model_dump())
    db.add(curriculum)
    await db.commit()
    await db.refresh(curriculum)

    return curriculum


@router.get("/", response_model=CurriculumListResponse)
async def list_curriculum(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    department_id: Optional[int] = Query(None, description="Filter by department ID"),
    year_level: Optional[int] = Query(None, ge=1, le=4, description="Filter by year level (1-4)"),
    semester_type: Optional[str] = Query(None, description="Filter by semester type (ODD/EVEN)"),
    course_id: Optional[int] = Query(None, description="Filter by course ID"),
    elective_group_id: Optional[int] = Query(None, description="Filter by elective group ID"),
    is_mandatory: Optional[bool] = Query(None, description="Filter by mandatory flag"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of all curriculum entries with optional filters.

    Supports filtering by department, year level, semester type, course, and elective group.
    Includes pagination.

    Args:
        skip: Pagination offset
        limit: Max results
        department_id: Filter by department
        year_level: Filter by year (1-4)
        semester_type: Filter by semester type (ODD/EVEN)
        course_id: Filter by course
        elective_group_id: Filter by elective group
        is_mandatory: Filter by mandatory flag
        db: Database session

    Returns:
        CurriculumListResponse: List of curriculum entries with total count
    """
    query = select(Curriculum)

    # Apply filters
    if department_id:
        query = query.where(Curriculum.department_id == department_id)
    if year_level:
        query = query.where(Curriculum.year_level == year_level)
    if semester_type:
        query = query.where(Curriculum.semester_type == semester_type)
    if course_id:
        query = query.where(Curriculum.course_id == course_id)
    if elective_group_id:
        query = query.where(Curriculum.elective_group_id == elective_group_id)
    if is_mandatory is not None:
        query = query.where(Curriculum.is_mandatory == is_mandatory)

    # Order and paginate
    query = query.order_by(
        Curriculum.department_id,
        Curriculum.year_level,
        Curriculum.semester_type,
        Curriculum.course_id,
        Curriculum.elective_group_id
    ).offset(skip).limit(limit)

    result = await db.execute(query)
    curriculum_entries = result.scalars().all()

    # Get total count
    count_query = select(func.count()).select_from(Curriculum)
    if department_id:
        count_query = count_query.where(Curriculum.department_id == department_id)
    if year_level:
        count_query = count_query.where(Curriculum.year_level == year_level)
    if semester_type:
        count_query = count_query.where(Curriculum.semester_type == semester_type)
    if course_id:
        count_query = count_query.where(Curriculum.course_id == course_id)
    if elective_group_id:
        count_query = count_query.where(Curriculum.elective_group_id == elective_group_id)
    if is_mandatory is not None:
        count_query = count_query.where(Curriculum.is_mandatory == is_mandatory)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    return CurriculumListResponse(data=curriculum_entries, total=total)


@router.get("/{curriculum_id}", response_model=CurriculumResponse)
async def get_curriculum(
    curriculum_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific curriculum entry by ID.

    Args:
        curriculum_id: Curriculum entry ID
        db: Database session

    Returns:
        CurriculumResponse: Curriculum entry details

    Raises:
        404: Curriculum entry not found
    """
    query = select(Curriculum).where(Curriculum.id == curriculum_id)
    result = await db.execute(query)
    curriculum = result.scalar_one_or_none()

    if not curriculum:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Curriculum entry with id {curriculum_id} not found"
        )

    return curriculum


@router.put("/{curriculum_id}", response_model=CurriculumResponse)
async def update_curriculum(
    curriculum_id: int,
    curriculum_update: CurriculumUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Update a curriculum entry.

    **Permissions:** Admin only

    Args:
        curriculum_id: Curriculum entry ID
        curriculum_update: Updated curriculum data
        db: Database session
        current_admin: Current admin user

    Returns:
        CurriculumResponse: Updated curriculum entry

    Raises:
        404: Curriculum entry not found
    """
    query = select(Curriculum).where(Curriculum.id == curriculum_id)
    result = await db.execute(query)
    curriculum = result.scalar_one_or_none()

    if not curriculum:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Curriculum entry with id {curriculum_id} not found"
        )

    update_data = curriculum_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(curriculum, field, value)

    await db.commit()
    await db.refresh(curriculum)

    return curriculum


@router.delete("/{curriculum_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_curriculum(
    curriculum_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Delete a curriculum entry.

    **Permissions:** Admin only

    Args:
        curriculum_id: Curriculum entry ID
        db: Database session
        current_admin: Current admin user

    Raises:
        404: Curriculum entry not found
    """
    query = select(Curriculum).where(Curriculum.id == curriculum_id)
    result = await db.execute(query)
    curriculum = result.scalar_one_or_none()

    if not curriculum:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Curriculum entry with id {curriculum_id} not found"
        )

    await db.delete(curriculum)
    await db.commit()

    return None
