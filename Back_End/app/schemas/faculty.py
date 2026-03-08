"""
Module: Faculty Management & Workload
Repository: timeweaver_backend
Owner: Meka Jahnavi

Pydantic schemas for Faculty and FacultyPreference models.
Used for request/response validation.

Dependencies:
    - pydantic (validation)
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class FacultyPreferenceBase(BaseModel):
    """Base schema for faculty preferences."""
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    time_slot_id: int = Field(..., gt=0, description="Time slot ID")
    preference_type: str = Field(..., description="'preferred' or 'not_available'")
    
    @validator('preference_type')
    def validate_preference_type(cls, v):
        """Validate preference type is one of allowed values."""
        if v not in ['preferred', 'not_available']:
            raise ValueError("preference_type must be 'preferred' or 'not_available'")
        return v


class FacultyPreferenceCreate(FacultyPreferenceBase):
    """Schema for creating faculty preference."""
    pass


class FacultyPreferenceResponse(FacultyPreferenceBase):
    """Schema for faculty preference response."""
    id: int
    faculty_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FacultyBase(BaseModel):
    """Base schema for faculty."""
    employee_id: str = Field(..., min_length=1, max_length=20, description="Unique employee ID")
    department_id: int = Field(..., gt=0, description="Department ID")
    designation: str = Field(default="Lecturer", max_length=50, description="Faculty designation")
    max_hours_per_week: int = Field(default=18, ge=1, le=50, description="Max teaching hours per week")


class FacultyCreate(FacultyBase):
    """Schema for creating faculty."""
    user_id: int = Field(..., gt=0, description="User ID")


class FacultyUpdate(BaseModel):
    """Schema for updating faculty."""
    designation: Optional[str] = Field(None, max_length=50)
    max_hours_per_week: Optional[int] = Field(None, ge=1, le=50)
    department_id: Optional[int] = Field(None, gt=0)


class FacultyResponse(FacultyBase):
    """Schema for faculty response."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FacultyDetailResponse(FacultyResponse):
    """Detailed faculty response with preferences."""
    preferences: List[FacultyPreferenceResponse] = []


class WorkloadResponse(BaseModel):
    """Schema for workload response."""
    faculty_id: int
    total_hours: int = Field(..., description="Total teaching hours")
    max_hours: int = Field(..., description="Maximum allowed hours")
    is_overloaded: bool = Field(..., description="Whether faculty is overloaded")
    utilization_percentage: float = Field(..., description="Utilization as percentage")
    section_count: int = Field(..., description="Number of sections assigned")


class WorkloadSummaryResponse(BaseModel):
    """Schema for workload summary response."""
    total_faculty: int
    overloaded_count: int
    average_utilization: float
    overloaded_faculty: List[int]
