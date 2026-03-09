"""
Module: Faculty Leave Schema Definitions
Repository: timeweaver_backend
Epic: 3 - Timetable Generation / Re-generation

Pydantic schemas for faculty leave and slot locking CRUD operations.
Supports time slot-based leave specification with full-day toggle.

User Stories: 3.6.2, 3.8.2 (Faculty Leave Handling)
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime
from app.models.faculty_leave import LeaveType, LeaveStrategy


class LeaveTimeSlotRequest(BaseModel):
    """Request to specify time slots for a leave"""
    leave_date: date = Field(..., description="Date for which time slots are specified", alias="date")
    start_time_slot_id: int = Field(..., gt=0, description="Starting time slot ID")
    end_time_slot_id: int = Field(..., gt=0, description="Ending time slot ID (inclusive)")

    @field_validator('end_time_slot_id')
    @classmethod
    def validate_slots(cls, v, info):
        """Ensure end slot >= start slot"""
        if 'start_time_slot_id' in info.data and v < info.data['start_time_slot_id']:
            raise ValueError('end_time_slot_id must be >= start_time_slot_id')
        return v


class LeaveAnalyzeRequest(BaseModel):
    """Request to analyze faculty leave impact with optional time slot specification"""
    faculty_id: int = Field(..., gt=0, description="Faculty member ID")
    timetable_id: int = Field(..., gt=0, description="Timetable ID")
    start_date: date = Field(..., description="Leave start date")
    end_date: date = Field(..., description="Leave end date")
    is_full_day: bool = Field(default=True, description="True if full day leave, False if partial")
    start_time_slot_id: Optional[int] = Field(None, gt=0, description="Starting time slot on start_date (if not full day)")
    end_time_slot_id: Optional[int] = Field(None, gt=0, description="Ending time slot on end_date (if not full day)")
    leave_type: LeaveType = Field(..., description="Type of leave")
    strategy: LeaveStrategy = Field(default=LeaveStrategy.WITHIN_SECTION_SWAP, description="Resolution strategy")

    @field_validator('end_date')
    @classmethod
    def validate_dates(cls, v, info):
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

    @field_validator('end_time_slot_id')
    @classmethod
    def validate_time_slots(cls, v, info):
        """Validate time slot constraints when not full day"""
        if info.data.get('is_full_day'):
            return v  # No time slot validation needed for full day

        if not info.data.get('is_full_day') and info.data.get('start_time_slot_id'):
            if v and v < info.data['start_time_slot_id']:
                raise ValueError('end_time_slot_id must be >= start_time_slot_id')
        return v


class LeaveCreateRequest(BaseModel):
    """Request to create faculty leave"""
    faculty_id: int = Field(..., gt=0, description="Faculty member ID")
    semester_id: int = Field(..., gt=0, description="Semester ID")
    timetable_id: Optional[int] = Field(None, gt=0, description="Timetable ID")
    start_date: date = Field(..., description="Leave start date")
    end_date: date = Field(..., description="Leave end date")
    is_full_day: bool = Field(default=True, description="True if full day leave")
    start_time_slot_id: Optional[int] = Field(None, gt=0, description="Starting time slot (if not full day)")
    end_time_slot_id: Optional[int] = Field(None, gt=0, description="Ending time slot (if not full day)")
    leave_type: LeaveType = Field(..., description="Type of leave")
    strategy: LeaveStrategy = Field(default=LeaveStrategy.WITHIN_SECTION_SWAP, description="Resolution strategy")
    reason: Optional[str] = Field(None, description="Leave reason/notes")
    replacement_faculty_id: Optional[int] = Field(None, gt=0, description="Optional replacement faculty")

    @field_validator('end_date')
    @classmethod
    def validate_dates(cls, v, info):
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class LeaveResponse(BaseModel):
    """Response schema for faculty leave"""
    id: int
    faculty_id: int
    semester_id: int
    timetable_id: Optional[int]
    start_date: date
    end_date: date
    is_full_day: bool
    start_time_slot_id: Optional[int]
    end_time_slot_id: Optional[int]
    affected_slot_ids: List[int]
    leave_type: str
    strategy: str
    status: str
    replacement_faculty_id: Optional[int]
    impact_analysis: Optional[dict]
    resolution_details: Optional[dict]
    reason: Optional[str]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime]
    applied_at: Optional[datetime]

    model_config = {"from_attributes": True}


class LeaveListResponse(BaseModel):
    """List response for faculty leaves with pagination"""
    data: List[LeaveResponse]
    total: int


class LeaveImpactResponse(BaseModel):
    """Response schema for leave impact analysis"""
    affected_slots: List[int] = Field(..., description="All slots affected by leave")
    affected_sections: List[int] = Field(..., description="Sections affected")
    locked_slots: List[int] = Field(..., description="Time slots that are locked (can't be changed)")
    locked_affected_slots: List[int] = Field(..., description="Intersection of affected and locked slots")
    swap_proposals: List[dict] = Field(..., description="Proposed faculty swaps")
    total_impact: int = Field(..., description="Total number of affected slots")
    swappable_slots: int = Field(..., description="Number of slots that can be swapped")
    locked_count: int = Field(..., description="Number of locked slots in affected range")
    analysis_timestamp: str = Field(..., description="When analysis was performed")


class SlotLockRequest(BaseModel):
    """Request to lock/unlock slots"""
    timetable_id: int = Field(..., gt=0, description="Timetable ID")
    slot_ids: List[int] = Field(..., min_length=1, description="Slot IDs to lock/unlock")


class SlotLockResponse(BaseModel):
    """Response for slot lock/unlock operation"""
    timetable_id: int
    locked_count: int
    slot_ids: List[int]
    message: str
