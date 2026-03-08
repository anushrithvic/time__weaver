"""
Module: Faculty-Course Assignment Schemas
Repository: timeweaver_backend
Epic: 4 - Faculty Management & Workload

Pydantic schemas for Faculty-Course assignment CRUD operations.
Used for request/response validation.

Dependencies:
    - pydantic (BaseModel, Field)
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FacultyCourseCreate(BaseModel):
    """Schema for creating a faculty-course assignment."""
    faculty_id: int = Field(..., gt=0, examples=[1])
    course_id: int = Field(..., gt=0, examples=[5])
    section_id: int = Field(..., gt=0, examples=[3])
    semester_id: int = Field(..., gt=0, examples=[1])
    is_primary: bool = Field(default=True, examples=[True])


class FacultyCourseUpdate(BaseModel):
    """Schema for updating a faculty-course assignment."""
    is_primary: Optional[bool] = None


class FacultyCourseResponse(BaseModel):
    """Schema for faculty-course assignment response."""
    id: int
    faculty_id: int
    course_id: int
    section_id: int
    semester_id: int
    is_primary: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class FacultyCourseDetail(BaseModel):
    """Detailed response with names for display."""
    id: int
    faculty_id: int
    faculty_name: Optional[str] = None
    employee_id: Optional[str] = None
    course_id: int
    course_code: Optional[str] = None
    course_name: Optional[str] = None
    section_id: int
    section_name: Optional[str] = None
    semester_id: int
    semester_name: Optional[str] = None
    is_primary: bool
    created_at: datetime

    model_config = {"from_attributes": True}
