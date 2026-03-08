"""
Module: Faculty Management & Workload
Repository: timeweaver_backend
Owner: Meka Jahnavi
Epic: 4 - Faculty Management & Workload

Faculty Preferences API endpoints.
Allows faculty to set time preferences (preferred/unavailable).

Dependencies:
    - app.models.faculty (Faculty, FacultyPreference models)
    - app.schemas.faculty (Pydantic schemas)
    - app.core.dependencies (get_current_user, get_current_faculty)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.faculty import Faculty, FacultyPreference
from app.models.user import User
from app.schemas.faculty import (
    FacultyPreferenceCreate, FacultyPreferenceResponse
)

router = APIRouter()


@router.post("/", response_model=FacultyPreferenceResponse, status_code=status.HTTP_201_CREATED)
async def set_faculty_preference(
    preference_data: FacultyPreferenceCreate,
    faculty_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> FacultyPreferenceResponse:
    """
    Set faculty time preference (faculty can set own, admin can set any).
    
    Args:
        preference_data: Preference data (day, time_slot, type)
        faculty_id: Faculty ID
        db: Database session
        current_user: Current user
        
    Returns:
        FacultyPreferenceResponse: Created preference
        
    Raises:
        HTTPException 403: If user trying to set preference for another faculty
        HTTPException 404: If faculty not found
        HTTPException 400: If preference already exists
        
    Test Coverage: tests/test_faculty.py::test_set_faculty_preference
    
    Example:
        POST /api/v1/faculty-preferences?faculty_id=1
        {
            "day_of_week": 0,
            "time_slot_id": 1,
            "preference_type": "not_available"
        }
    """
    # Check if faculty exists
    faculty = await db.get(Faculty, faculty_id)
    if not faculty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faculty not found"
        )
    
    # Check authorization (faculty can only set own preferences)
    if faculty.user_id != current_user.id:
        # Check if user is admin
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot set preferences for another faculty"
            )
    
    # Check if preference already exists for this day/time slot
    query = select(FacultyPreference).where(
        and_(
            FacultyPreference.faculty_id == faculty_id,
            FacultyPreference.day_of_week == preference_data.day_of_week,
            FacultyPreference.time_slot_id == preference_data.time_slot_id
        )
    )
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        # Update existing preference
        existing.preference_type = preference_data.preference_type
        await db.commit()
        await db.refresh(existing)
        return existing
    
    # Create new preference
    preference = FacultyPreference(
        faculty_id=faculty_id,
        **preference_data.model_dump()
    )
    db.add(preference)
    await db.commit()
    await db.refresh(preference)
    
    return preference


@router.get("/", response_model=List[FacultyPreferenceResponse])
async def get_faculty_preferences(
    faculty_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
) -> List[FacultyPreferenceResponse]:
    """
    Get all preferences for a faculty member.
    
    Args:
        faculty_id: Faculty ID (query parameter)
        db: Database session
        _: Current user
        
    Returns:
        List[FacultyPreferenceResponse]: All preferences for faculty
        
    Test Coverage: tests/test_faculty.py::test_get_faculty_preferences
    
    Example:
        GET /api/v1/faculty-preferences?faculty_id=1
    """
    query = select(FacultyPreference).where(FacultyPreference.faculty_id == faculty_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{preference_id}", response_model=FacultyPreferenceResponse)
async def get_preference(
    preference_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
) -> FacultyPreferenceResponse:
    """
    Get a specific preference by ID.
    
    Args:
        preference_id: Preference ID
        db: Database session
        _: Current user
        
    Returns:
        FacultyPreferenceResponse: Preference details
        
    Raises:
        HTTPException 404: If preference not found
        
    Test Coverage: tests/test_faculty.py::test_get_preference
    """
    preference = await db.get(FacultyPreference, preference_id)
    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preference not found"
        )
    return preference


@router.put("/{preference_id}", response_model=FacultyPreferenceResponse)
async def update_preference(
    preference_id: int,
    preference_data: FacultyPreferenceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> FacultyPreferenceResponse:
    """
    Update a preference (faculty can update own, admin can update any).
    
    Args:
        preference_id: Preference ID
        preference_data: Updated data
        db: Database session
        current_user: Current user
        
    Returns:
        FacultyPreferenceResponse: Updated preference
        
    Raises:
        HTTPException 403: If not authorized
        HTTPException 404: If preference not found
        
    Test Coverage: tests/test_faculty.py::test_update_preference
    """
    preference = await db.get(FacultyPreference, preference_id)
    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preference not found"
        )
    
    # Check authorization
    faculty = await db.get(Faculty, preference.faculty_id)
    if faculty.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this preference"
        )
    
    for key, value in preference_data.model_dump().items():
        setattr(preference, key, value)
    
    await db.commit()
    await db.refresh(preference)
    return preference


@router.delete("/{preference_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_preference(
    preference_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete a preference (faculty can delete own, admin can delete any).
    
    Args:
        preference_id: Preference ID
        db: Database session
        current_user: Current user
        
    Raises:
        HTTPException 403: If not authorized
        HTTPException 404: If preference not found
        
    Test Coverage: tests/test_faculty.py::test_delete_preference
    """
    preference = await db.get(FacultyPreference, preference_id)
    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preference not found"
        )
    
    # Check authorization
    faculty = await db.get(Faculty, preference.faculty_id)
    if faculty.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this preference"
        )
    
    await db.delete(preference)
    await db.commit()
