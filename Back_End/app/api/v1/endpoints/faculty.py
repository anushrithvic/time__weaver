"""
Module: Faculty Management & Workload
Repository: timeweaver_backend
Owner: Meka Jahnavi
Epic: 4 - Faculty Management & Workload

Faculty API endpoints for CRUD operations and workload management.

Dependencies:
    - app.models.faculty (Faculty model)
    - app.schemas.faculty (Pydantic schemas)
    - app.core.dependencies (get_current_user, get_current_admin)
    - app.services.workload_calculator (WorkloadCalculator)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_db
from app.core.dependencies import get_current_user, get_current_admin
from app.models.faculty import Faculty
from app.models.user import User
from app.schemas.faculty import (
    FacultyCreate, FacultyUpdate, FacultyResponse,
    FacultyDetailResponse, WorkloadResponse, WorkloadSummaryResponse
)
from app.services.workload_calculator import WorkloadCalculator

router = APIRouter()


@router.post("/", response_model=FacultyResponse, status_code=status.HTTP_201_CREATED,
              deprecated=True)
async def create_faculty(
    faculty_data: FacultyCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
) -> FacultyResponse:
    """
    **DEPRECATED** — Use `POST /api/v1/users/create-faculty` instead.
    
    That endpoint creates both the User account and Faculty profile in one step.
    This endpoint is kept only for backward compatibility and requires a pre-existing user_id.
    """
    # Verify the user exists and has faculty role
    query = select(User).where(User.id == faculty_data.user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {faculty_data.user_id} not found. "
                   f"Use POST /api/v1/users/create-faculty to create both user and faculty in one step."
        )
    
    # Check if faculty already exists for this user
    query = select(Faculty).where(Faculty.user_id == faculty_data.user_id)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Faculty profile already exists for this user"
        )
    
    # Check if employee_id is unique
    query = select(Faculty).where(Faculty.employee_id == faculty_data.employee_id)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee ID already exists"
        )
    
    # Create faculty
    faculty = Faculty(**faculty_data.model_dump())
    db.add(faculty)
    await db.commit()
    await db.refresh(faculty)
    
    return faculty


@router.get("/", response_model=List[FacultyResponse])
async def list_faculty(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
) -> List[FacultyResponse]:
    """
    List all faculty members (admin only).
    
    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum records to return
        db: Database session
        _: Current admin user
        
    Returns:
        List[FacultyResponse]: List of faculty
        
    Test Coverage: tests/test_faculty.py::test_list_faculty
    """
    query = select(Faculty).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{faculty_id}", response_model=FacultyDetailResponse)
async def get_faculty(
    faculty_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
) -> FacultyDetailResponse:
    """
    Get faculty details with preferences.
    
    Args:
        faculty_id: Faculty ID
        db: Database session
        _: Current user
        
    Returns:
        FacultyDetailResponse: Faculty with preferences
        
    Raises:
        HTTPException 404: If faculty not found
        
    Test Coverage: tests/test_faculty.py::test_get_faculty
    """
    faculty = await db.get(Faculty, faculty_id)
    if not faculty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faculty not found"
        )
    return faculty


@router.put("/{faculty_id}", response_model=FacultyResponse)
async def update_faculty(
    faculty_id: int,
    faculty_data: FacultyUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
) -> FacultyResponse:
    """
    Update faculty profile (admin only).
    
    Args:
        faculty_id: Faculty ID
        faculty_data: Update data
        db: Database session
        admin: Current admin user
        
    Returns:
        FacultyResponse: Updated faculty
        
    Raises:
        HTTPException 404: If faculty not found
        
    Test Coverage: tests/test_faculty.py::test_update_faculty
    """
    faculty = await db.get(Faculty, faculty_id)
    if not faculty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faculty not found"
        )
    
    for key, value in faculty_data.model_dump(exclude_unset=True).items():
        setattr(faculty, key, value)
    
    await db.commit()
    await db.refresh(faculty)
    return faculty


@router.delete("/{faculty_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_faculty(
    faculty_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
) -> None:
    """
    Delete faculty profile (admin only).
    
    Args:
        faculty_id: Faculty ID
        db: Database session
        admin: Current admin user
        
    Raises:
        HTTPException 404: If faculty not found
        
    Test Coverage: tests/test_faculty.py::test_delete_faculty
    """
    faculty = await db.get(Faculty, faculty_id)
    if not faculty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faculty not found"
        )
    
    await db.delete(faculty)
    await db.commit()


@router.get("/{faculty_id}/workload", response_model=WorkloadResponse)
async def get_faculty_workload(
    faculty_id: int,
    semester_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
) -> WorkloadResponse:
    """
    Get faculty teaching workload for a semester.
    
    Calculates total hours and checks if overloaded.
    
    Args:
        faculty_id: Faculty ID
        semester_id: Semester ID (query parameter)
        db: Database session
        _: Current user
        
    Returns:
        WorkloadResponse: Workload information
        
    Raises:
        HTTPException 404: If faculty not found
        
    Test Coverage: tests/test_faculty.py::test_get_faculty_workload
    
    Example:
        GET /api/v1/faculty/1/workload?semester_id=1
        
        Response:
        {
            "faculty_id": 1,
            "total_hours": 15,
            "max_hours": 18,
            "is_overloaded": false,
            "utilization_percentage": 83.33,
            "section_count": 3
        }
    """
    # Check if faculty exists
    faculty = await db.get(Faculty, faculty_id)
    if not faculty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faculty not found"
        )
    
    try:
        workload = await WorkloadCalculator.calculate_workload(faculty_id, semester_id, db)
        return workload
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
