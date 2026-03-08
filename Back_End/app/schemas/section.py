from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class SectionBase(BaseModel):
    """Base Section schema - permanent batch-based sections"""
    department_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=50, examples=["CSE-A"])
    batch_year_start: int = Field(..., ge=2020, le=2100, examples=[2023])
    batch_year_end: int = Field(..., ge=2020, le=2100, examples=[2027])
    student_count: int = Field(..., gt=0, examples=[60])
    dedicated_room_id: Optional[int] = Field(None, gt=0, description="Home room for HomeRoomPreference constraint")
    class_advisor_ids: Optional[list[int]] = Field(default=[], description="User IDs of class advisors for mentoring")


class SectionCreate(SectionBase):
    """Schema for creating a section"""
    pass


class SectionUpdate(BaseModel):
    """Schema for updating a section"""
    department_id: Optional[int] = Field(None, gt=0)
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    batch_year_start: Optional[int] = Field(None, ge=2020, le=2100)
    batch_year_end: Optional[int] = Field(None, ge=2020, le=2100)
    student_count: Optional[int] = Field(None, gt=0)
    dedicated_room_id: Optional[int] = Field(None, gt=0)
    class_advisor_ids: Optional[list[int]] = None


class SectionResponse(SectionBase):
    """Schema for section responses"""
    id: int
    
    model_config = ConfigDict(from_attributes=True)


class SectionListResponse(BaseModel):
    """Schema for listing sections"""
    data: list[SectionResponse]
    total: int
