"""
Module: Faculty Leave & Slot Locking API Endpoints (Module 3)
Repository: timeweaver_backend
Owner: Pranathi Nibhanipudi
Epic: 3 - Timetable Generation / Re-generation

REST API endpoints for faculty leave impact analysis and slot locking.

Key Endpoints (Faculty Leave):
    POST   /api/v1/faculty-leaves/analyze - Analyze leave impact
    POST   /api/v1/faculty-leaves - Create leave record
    GET    /api/v1/faculty-leaves - List leaves
    GET    /api/v1/faculty-leaves/{id} - Get leave details
    PATCH  /api/v1/faculty-leaves/{id}/approve - Approve leave
    PATCH  /api/v1/faculty-leaves/{id}/apply - Apply leave changes

Key Endpoints (Slot Locking):
    POST   /api/v1/slot-locks/lock - Lock slots
    POST   /api/v1/slot-locks/unlock - Unlock slots
    GET    /api/v1/slot-locks/locked - Get locked slots

Dependencies:
    - app.services.leave_impact_analyzer (LeaveImpactAnalyzer)
    - app.services.slot_locking_service (SlotLockingService)
    - app.models.faculty_leave (FacultyLeave, LeaveType, LeaveStrategy, LeaveStatus)

User Stories: 3.2.2 (Slot Locking), 3.6.2 & 3.8.2 (Faculty Leave)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import date, datetime

from app.db.session import get_db
from app.models.user import User, UserRole
from app.core.dependencies import get_current_admin, get_current_user
from app.models.faculty_leave import FacultyLeave, LeaveType, LeaveStrategy, LeaveStatus
from app.models.timetable import Timetable, TimetableSlot
from app.services.leave_impact_analyzer import LeaveImpactAnalyzer
from app.services.slot_locking_service import SlotLockingService
from pydantic import BaseModel, Field, validator

# Create two routers
leaves_router = APIRouter()
locks_router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class LeaveAnalyzeRequest(BaseModel):
    """Request to analyze faculty leave impact"""
    faculty_id: int = Field(..., gt=0, description="Faculty member ID")
    timetable_id: int = Field(..., gt=0, description="Timetable ID")
    start_date: date = Field(..., description="Leave start date")
    end_date: date = Field(..., description="Leave end date")
    leave_type: LeaveType = Field(..., description="Type of leave")
    strategy: LeaveStrategy = Field(default=LeaveStrategy.WITHIN_SECTION_SWAP, description="Resolution strategy")
    
    @validator('end_date')
    def end_after_start(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class LeaveCreateRequest(BaseModel):
    """Request to create faculty leave"""
    faculty_id: int = Field(..., gt=0)
    semester_id: int = Field(..., gt=0)
    timetable_id: Optional[int] = Field(None, gt=0)
    start_date: date
    end_date: date
    leave_type: LeaveType
    strategy: LeaveStrategy = LeaveStrategy.WITHIN_SECTION_SWAP
    reason: Optional[str] = None
    replacement_faculty_id: Optional[int] = Field(None, gt=0, description="Optional replacement faculty")
    
    @validator('end_date')
    def end_after_start(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
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
    leave_type: str
    strategy: str
    status: str
    replacement_faculty_id: Optional[int]
    impact_analysis: Optional[dict]
    resolution_details: Optional[dict]
    reason: Optional[str]
    created_by: Optional[int]
    created_at: datetime
    approved_at: Optional[datetime]
    applied_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class LeaveImpactResponse(BaseModel):
    """Response schema for leave impact analysis"""
    affected_slots: list[int]
    affected_sections: list[int]
    locked_slots: list[int]
    locked_affected_slots: list[int]
    swap_proposals: list[dict]
    total_impact: int
    swappable_slots: int
    locked_count: int
    analysis_timestamp: str


class SlotLockRequest(BaseModel):
    """Request to lock/unlock slots"""
    timetable_id: int = Field(..., gt=0, description="Timetable ID")
    slot_ids: list[int] = Field(..., min_items=1, description="Slot IDs to lock/unlock")


class SlotLockResponse(BaseModel):
    """Response for slot lock/unlock operation"""
    timetable_id: int
    locked_count: int
    slot_ids: list[int]
    message: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_error_response(error: str, message: str, code: int):
    """Create structured error response"""
    return {
        "error": error,
        "message": message,
        "code": code
    }


# ============================================================================
# FACULTY LEAVE ENDPOINTS
# ============================================================================

@leaves_router.post("/analyze", response_model=LeaveImpactResponse)
async def analyze_leave_impact(
    request: LeaveAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze the impact of a faculty leave before creating it.
    
    Returns affected slots, locked slots, and swap proposals.
    
    **Epic 3: User Stories 3.6.2, 3.8.2** - Faculty Leave Handling
    **Permissions:** Faculty (own leave) or Admin
    
    Args:
        request: Leave analysis parameters
        db: Database session
        current_user: Current user
        
    Returns:
        LeaveImpactResponse: Impact analysis with swap proposals
        
    Example:
        ```
        POST /api/v1/faculty-leaves/analyze
        {
            "faculty_id": 10,
            "timetable_id": 5,
            "start_date": "2024-10-01",
            "end_date": "2024-10-07",
            "leave_type": "SICK",
            "strategy": "WITHIN_SECTION_SWAP"
        }
        ```
    """
    # Permission check: Faculty can only analyze own leave
    if current_user.role == UserRole.FACULTY and current_user.id != request.faculty_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                "FORBIDDEN",
                "Faculty can only analyze their own leave",
                403
            )
        )
    
    # Validate timetable exists
    timetable_query = select(Timetable).where(Timetable.id == request.timetable_id)
    timetable_result = await db.execute(timetable_query)
    timetable = timetable_result.scalar_one_or_none()
    
    if not timetable:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                "NOT_FOUND",
                f"Timetable with id {request.timetable_id} not found",
                404
            )
        )

    # Create temporary leave object for analysis
    leave = FacultyLeave(
        faculty_id=request.faculty_id,
        semester_id=timetable.semester_id,  # Set correct semester from timetable
        timetable_id=request.timetable_id,
        start_date=request.start_date,
        end_date=request.end_date,
        leave_type=request.leave_type,
        strategy=request.strategy,
        status=LeaveStatus.PROPOSED
    )
    
    # Analyze impact
    analyzer = LeaveImpactAnalyzer(db)
    try:
        impact = analyzer.analyze_leave_impact(leave)
        return LeaveImpactResponse(**impact)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                "ANALYSIS_ERROR",
                f"Error analyzing leave impact: {str(e)}",
                500
            )
        )


@leaves_router.post("/", response_model=LeaveResponse, status_code=status.HTTP_201_CREATED)
async def create_leave(
    request: LeaveCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new faculty leave record with impact analysis.
    
    Status starts as PROPOSED. Admin must approve before applying.
    
    **Permissions:** Faculty (own leave) or Admin
    
    Args:
        request: Leave details
        db: Database session
        current_user: Current user
        
    Returns:
        LeaveResponse: Created leave with impact analysis
        
    Example:
        ```
        POST /api/v1/faculty-leaves
        {
            "faculty_id": 10,
            "semester_id": 1,
            "timetable_id": 5,
            "start_date": "2024-10-01",
            "end_date": "2024-10-07",
            "leave_type": "SICK",
            "strategy": "WITHIN_SECTION_SWAP",
            "reason": "Medical emergency"
        }
        ```
    """
    # Permission check
    if current_user.role == UserRole.FACULTY and current_user.id != request.faculty_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                "FORBIDDEN",
                "Faculty can only create their own leave",
                403
            )
        )
    
    # Create leave
    leave = FacultyLeave(
        **request.model_dump(),
        status=LeaveStatus.PROPOSED,
        created_by=current_user.id
    )
    
    # Analyze impact if timetable provided
    if leave.timetable_id:
        analyzer = LeaveImpactAnalyzer(db)
        try:
            impact = analyzer.analyze_leave_impact(leave)
            leave.impact_analysis = impact
        except Exception as e:
            # Continue without impact analysis if error
            leave.impact_analysis = {"error": str(e)}
    
    db.add(leave)
    await db.commit()
    await db.refresh(leave)
    
    return leave


@leaves_router.get("/", response_model=list[LeaveResponse])
async def list_leaves(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    faculty_id: Optional[int] = Query(None, description="Filter by faculty"),
    semester_id: Optional[int] = Query(None, description="Filter by semester"),
    status: Optional[LeaveStatus] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List faculty leaves with optional filters.
    
    **Permissions:** Faculty (own leaves) or Admin (all leaves)
    
    Example:
        ```
        GET /api/v1/faculty-leaves?semester_id=1&status=PROPOSED
        ```
    """
    query = select(FacultyLeave)
    
    # Faculty can only see their own leaves
    if current_user.role == UserRole.FACULTY:
        query = query.where(FacultyLeave.faculty_id == current_user.id)
    elif faculty_id:  # Admin filter
        query = query.where(FacultyLeave.faculty_id == faculty_id)
    
    if semester_id:
        query = query.where(FacultyLeave.semester_id == semester_id)
    if status:
        query = query.where(FacultyLeave.status == status)
    
    query = query.order_by(FacultyLeave.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    leaves = result.scalars().all()
    
    return leaves


@leaves_router.get("/{leave_id}", response_model=LeaveResponse)
async def get_leave(
    leave_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific faculty leave by ID"""
    query = select(FacultyLeave).where(FacultyLeave.id == leave_id)
    result = await db.execute(query)
    leave = result.scalar_one_or_none()
    
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response("NOT_FOUND", f"Leave with id {leave_id} not found", 404)
        )
    
    # Permission check
    if current_user.role == UserRole.FACULTY and current_user.id != leave.faculty_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response("FORBIDDEN", "Cannot view other faculty's leave", 403)
        )
    
    return leave


@leaves_router.patch("/{leave_id}/approve", response_model=LeaveResponse)
async def approve_leave(
    leave_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Approve a faculty leave (admin only).
    
    Changes status from PROPOSED to APPROVED.
    
    **Permissions:** Admin only
    """
    query = select(FacultyLeave).where(FacultyLeave.id == leave_id)
    result = await db.execute(query)
    leave = result.scalar_one_or_none()
    
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response("NOT_FOUND", f"Leave with id {leave_id} not found", 404)
        )
    
    if leave.status != LeaveStatus.PROPOSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                "INVALID_STATUS",
                f"Can only approve PROPOSED leaves. Current status: {leave.status}",
                400
            )
        )
    
    leave.status = LeaveStatus.APPROVED
    leave.approved_at = datetime.now()
    
    await db.commit()
    await db.refresh(leave)
    
    return leave


@leaves_router.patch("/{leave_id}/apply", response_model=LeaveResponse)
async def apply_leave_changes(
    leave_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Apply leave changes to timetable (admin only).
    
    Executes the swap proposals from impact analysis.
    Changes status from APPROVED to APPLIED.
    
    **Permissions:** Admin only
    """
    query = select(FacultyLeave).where(FacultyLeave.id == leave_id)
    result = await db.execute(query)
    leave = result.scalar_one_or_none()
    
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response("NOT_FOUND", f"Leave with id {leave_id} not found", 404)
        )
    
    if leave.status != LeaveStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                "INVALID_STATUS",
                f"Can only apply APPROVED leaves. Current status: {leave.status}",
                400
            )
        )
    
    # TODO: Apply swap proposals from impact_analysis
    # This would use the swap proposals to update TimetableSlot assignments
    
    leave.status = LeaveStatus.APPLIED
    leave.applied_at = datetime.now()
    leave.resolution_details = {
        "applied_at": str(datetime.now()),
        "applied_by": current_admin.id
    }
    
    await db.commit()
    await db.refresh(leave)
    
    return leave


# ============================================================================
# SLOT LOCKING ENDPOINTS
# ============================================================================

@locks_router.post("/lock", response_model=SlotLockResponse)
async def lock_slots(
    request: SlotLockRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Lock specified timetable slots.
    
    Locked slots cannot be modified during re-optimization.
    
    **Epic 3: User Story 3.2.2** - Slot Locking
    **Permissions:** Admin only
    
    Example:
        ```
        POST /api/v1/slot-locks/lock
        {
            "timetable_id": 5,
            "slot_ids": [1, 2, 3, 4]
        }
        ```
    """
    service = SlotLockingService(db)
    
    try:
        result = await service.lock_slots(request.timetable_id, request.slot_ids)
        
        return SlotLockResponse(
            timetable_id=request.timetable_id,
            locked_count=result["locked_count"],
            slot_ids=result["slot_ids"],
            message=f"Successfully locked {result['locked_count']} slots"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response("NOT_FOUND", str(e), 404)
        )


@locks_router.post("/unlock", response_model=SlotLockResponse)
async def unlock_slots(
    request: SlotLockRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Unlock specified timetable slots.
    
    **Permissions:** Admin only
    
    Example:
        ```
        POST /api/v1/slot-locks/unlock
        {
            "timetable_id": 5,
            "slot_ids": [1, 2, 3, 4]
        }
        ```
    """
    service = SlotLockingService(db)
    
    try:
        result = await service.unlock_slots(request.timetable_id, request.slot_ids)
        
        return SlotLockResponse(
            timetable_id=request.timetable_id,
            locked_count=result["unlocked_count"],
            slot_ids=result["slot_ids"],
            message=f"Successfully unlocked {result['unlocked_count']} slots"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response("NOT_FOUND", str(e), 404)
        )


@locks_router.get("/locked")
async def get_locked_slots(
    timetable_id: int = Query(..., gt=0, description="Timetable ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all locked slots for a timetable.
    
    **Permissions:** All authenticated users
    
    Example:
        ```
        GET /api/v1/slot-locks/locked?timetable_id=5
        ```
    """
    service = SlotLockingService(db)
    
    try:
        result = await service.get_locked_slots(timetable_id)
        
        return {
            "timetable_id": timetable_id,
            "locked_slots": result["locked_slots"],
            "total_locked": result["total_locked"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response("NOT_FOUND", str(e), 404)
        )
