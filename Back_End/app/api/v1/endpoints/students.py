"""
Student Management API Endpoints

CRUD operations for student profiles.
Student creation is typically done via the unified POST /users/create-student endpoint,
but this router provides direct CRUD for managing existing student profiles.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_db
from app.core.dependencies import get_current_user, get_current_admin
from app.models.student import Student
from app.models.user import User
from app.schemas.student import (
    StudentCreate, StudentUpdate, StudentResponse
)

router = APIRouter()


@router.get("/", response_model=List[StudentResponse])
async def list_students(
    skip: int = 0,
    limit: int = 100,
    department_id: int = None,
    section_id: int = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
) -> List[StudentResponse]:
    """
    List all students with optional filters (admin only).
    
    Query Parameters:
        skip: Pagination offset
        limit: Max records to return
        department_id: Filter by department
        section_id: Filter by section
    """
    query = select(Student)
    if department_id:
        query = query.where(Student.department_id == department_id)
    if section_id:
        query = query.where(Student.section_id == section_id)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
) -> StudentResponse:
    """Get student details by ID."""
    student = await db.get(Student, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    return student


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: int,
    student_data: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
) -> StudentResponse:
    """Update student profile (admin only)."""
    student = await db.get(Student, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    for key, value in student_data.model_dump(exclude_unset=True).items():
        setattr(student, key, value)
    
    await db.commit()
    await db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
) -> None:
    """Delete student profile (admin only)."""
    student = await db.get(Student, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    await db.delete(student)
    await db.commit()
