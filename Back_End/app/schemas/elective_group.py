from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class ElectiveGroupBase(BaseModel):
    """Base ElectiveGroup schema - permanent groups"""
    name: str = Field(..., min_length=1, max_length=100, examples=["PE1", "FE1-EVS"])
    description: Optional[str] = Field(None, examples=["Professional Elective Group 1"])
    participating_department_ids: Optional[list[int]] = Field(default=[], description="Department IDs for cross-department electives (FE)")


class ElectiveGroupCreate(ElectiveGroupBase):
    """Schema for creating an elective group"""
    pass


class ElectiveGroupUpdate(BaseModel):
    """Schema for updating an elective group"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    participating_department_ids: Optional[list[int]] = None


class ElectiveGroupResponse(ElectiveGroupBase):
    """Schema for elective group responses"""
    id: int
    
    model_config = ConfigDict(from_attributes=True)


class ElectiveGroupListResponse(BaseModel):
    """Schema for listing elective groups"""
    data: list[ElectiveGroupResponse]
    total: int
