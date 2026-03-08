from pydantic import BaseModel, Field, ConfigDict
from datetime import date, datetime
from typing import Optional
from app.models.semester import SemesterType


class SemesterBase(BaseModel):
    """
    Base Semester schema - shared properties
    """
    name: str = Field(..., min_length=1, max_length=100, examples=["Fall 2026"])
    academic_year: str = Field(..., pattern=r"^\d{4}-\d{4}$", examples=["2026-2027"])
    semester_type: SemesterType = Field(..., description="ODD or EVEN semester type")
    start_date: date
    end_date: date
    is_active: bool = True


class SemesterCreate(SemesterBase):
    """
    Schema for creating a semester
    """
    pass


class SemesterUpdate(BaseModel):
    """
    Schema for updating a semester - all fields optional
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    academic_year: Optional[str] = Field(None, pattern=r"^\d{4}-\d{4}$")
    semester_type: Optional[SemesterType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class SemesterResponse(SemesterBase):
    """
    Schema for semester responses - includes database fields
    """
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    semester_type: str
    
    model_config = ConfigDict(from_attributes=True)


class SemesterListResponse(BaseModel):
    """
    Schema for listing semesters with pagination
    """
    data: list[SemesterResponse]
    total: int
