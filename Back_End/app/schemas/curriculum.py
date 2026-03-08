"""
Pydantic schemas for Epic 3 Phase 2 new models:
- Curriculum
- CourseElectiveAssignment
- CourseBatchingConfig
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from app.models.semester import SemesterType


# ===============================
# Curriculum Schemas
# ===============================

class CurriculumBase(BaseModel):
    """Base Curriculum schema"""
    department_id: int = Field(..., gt=0)
    year_level: int = Field(..., ge=1, le=4, description="Academic year level (1-4)")
    semester_type: SemesterType = Field(..., description="ODD or EVEN semester")
    course_id: int = Field(..., gt=0)
    is_mandatory: bool = Field(default=True, description="True for CORE courses, False for electives")


class CurriculumCreate(CurriculumBase):
    """Schema for creating a curriculum entry"""
    pass


class CurriculumUpdate(BaseModel):
    """Schema for updating a curriculum entry"""
    department_id: Optional[int] = Field(None, gt=0)
    year_level: Optional[int] = Field(None, ge=1, le=4)
    semester_type: Optional[SemesterType] = None
    course_id: Optional[int] = Field(None, gt=0)
    is_mandatory: Optional[bool] = None


class CurriculumResponse(CurriculumBase):
    """Schema for curriculum responses"""
    id: int
    
    model_config = ConfigDict(from_attributes=True)


class CurriculumListResponse(BaseModel):
    """Schema for listing curriculum entries"""
    data: list[CurriculumResponse]
    total: int


# ===============================
# CourseElectiveAssignment Schemas
# ===============================

class CourseElectiveAssignmentBase(BaseModel):
    """Base CourseElectiveAssignment schema"""
    elective_group_id: int = Field(..., gt=0, description="Elective group (PE1, PE2, FE1)")
    semester_id: int = Field(..., gt=0, description="Semester offering this course")
    course_id: int = Field(..., gt=0, description="Course being offered")
    assigned_room_id: Optional[int] = Field(None, gt=0, description="Pre-assigned room for PE sync")


class CourseElectiveAssignmentCreate(CourseElectiveAssignmentBase):
    """Schema for creating a course elective assignment"""
    pass


class CourseElectiveAssignmentUpdate(BaseModel):
    """Schema for updating a course elective assignment"""
    elective_group_id: Optional[int] = Field(None, gt=0)
    semester_id: Optional[int] = Field(None, gt=0)
    course_id: Optional[int] = Field(None, gt=0)
    assigned_room_id: Optional[int] = Field(None, gt=0)


class CourseElectiveAssignmentResponse(CourseElectiveAssignmentBase):
    """Schema for course elective assignment responses"""
    id: int
    
    model_config = ConfigDict(from_attributes=True)


class CourseElectiveAssignmentListResponse(BaseModel):
    """Schema for listing course elective assignments"""
    data: list[CourseElectiveAssignmentResponse]
    total: int


# ===============================
# CourseBatchingConfig Schemas
# ===============================

class CourseBatchingConfigBase(BaseModel):
    """Base CourseBatchingConfig schema"""
    course_id: int = Field(..., gt=0, description="Lab course requiring batching")
    semester_id: int = Field(..., gt=0, description="Semester for this batching config")
    num_batches: int = Field(..., ge=1, le=10, description="Number of batches (1-10)")
    batch_size: int = Field(..., gt=0, description="Students per batch")


class CourseBatchingConfigCreate(CourseBatchingConfigBase):
    """Schema for creating a course batching config"""
    pass


class CourseBatchingConfigUpdate(BaseModel):
    """Schema for updating a course batching config"""
    course_id: Optional[int] = Field(None, gt=0)
    semester_id: Optional[int] = Field(None, gt=0)
    num_batches: Optional[int] = Field(None, ge=1, le=10)
    batch_size: Optional[int] = Field(None, gt=0)


class CourseBatchingConfigResponse(CourseBatchingConfigBase):
    """Schema for course batching config responses"""
    id: int
    
    model_config = ConfigDict(from_attributes=True)


class CourseBatchingConfigListResponse(BaseModel):
    """Schema for listing course batching configs"""
    data: list[CourseBatchingConfigResponse]
    total: int
