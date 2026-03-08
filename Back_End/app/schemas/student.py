"""
Pydantic schemas for Student model.

Used for request/response validation in student CRUD operations.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class StudentBase(BaseModel):
    """Base schema for student."""
    roll_no: str = Field(..., min_length=1, max_length=20, description="Unique roll number")
    department_id: int = Field(..., gt=0, description="Department ID")
    section_id: int = Field(..., gt=0, description="Section ID")


class StudentCreate(StudentBase):
    """Schema for creating a student profile (requires existing user_id)."""
    user_id: int = Field(..., gt=0, description="User ID")


class StudentUpdate(BaseModel):
    """Schema for updating a student profile."""
    department_id: Optional[int] = Field(None, gt=0)
    section_id: Optional[int] = Field(None, gt=0)


class StudentResponse(StudentBase):
    """Schema for student response."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
