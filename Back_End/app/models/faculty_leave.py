"""
Module: Timetable Generation & Scheduling (Module 3)
Repository: timeweaver_backend
Owner: Pranathi Nibhanipudi
Epic: 3 - Timetable Generation / Re-generation

FacultyLeave Model

Tracks faculty leave periods and their impact on timetables.
Supports short-term, medium-term, and long-term leaves.
Status workflow: proposed → approved → applied

Key Fields:
    - faculty_id: User on leave
    - leave_type: SICK, CASUAL, MATERNITY, SABBATICAL
    - strategy: SWAP, REDISTRIBUTE, REPLACEMENT, CANCEL
    - status: PROPOSED, APPROVED, APPLIED, REJECTED
    - impact_analysis: JSON with affected slots and swap proposals

Dependencies:
    - app.models.timetable (Timetable, TimetableSlot)
    - Module 4: User model (faculty)

User Stories: 3.6, 3.8
"""

from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, ForeignKey, JSON, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.db.session import Base


class LeaveType(str, enum.Enum):
    """Types of faculty leave"""
    SICK = "SICK"
    CASUAL = "CASUAL"
    MATERNITY = "MATERNITY"
    PATERNITY = "PATERNITY"
    SABBATICAL = "SABBATICAL"
    STUDY = "STUDY"
    EMERGENCY = "EMERGENCY"
    OTHER = "OTHER"


class LeaveStrategy(str, enum.Enum):
    """Strategies for handling leave"""
    WITHIN_SECTION_SWAP = "WITHIN_SECTION_SWAP"  # Swap with section faculty
    REDISTRIBUTE = "REDISTRIBUTE"                 # Spread among multiple faculty
    REPLACEMENT = "REPLACEMENT"                   # Assign replacement faculty
    CANCEL = "CANCEL"                            # Cancel classes
    MANUAL = "MANUAL"                            # Admin handles manually


class LeaveStatus(str, enum.Enum):
    """Leave application status"""
    PROPOSED = "PROPOSED"      # Initial proposal with impact analysis
    APPROVED = "APPROVED"      # Approved by admin
    APPLIED = "APPLIED"        # Changes applied to timetable
    REJECTED = "REJECTED"      # Not approved
    CANCELLED = "CANCELLED"    # Leave cancelled


class FacultyLeave(Base):
    """
    Faculty leave record with impact analysis and resolution tracking.
    
    Workflow:
    1. Create leave record → status = PROPOSED
    2. System analyzes impact → stores in impact_analysis
    3. Admin reviews proposal → status = APPROVED/REJECTED
    4. Apply changes to timetable → status = APPLIED
    
    Attributes:
        id (int): Primary key
        faculty_id (int): Faculty member on leave
        semester_id (int): Affected semester
        timetable_id (int): Affected timetable (optional)
        start_date (date): Leave start date
        end_date (date): Leave end date
        leave_type (LeaveType): Type of leave
        strategy (LeaveStrategy): Chosen resolution strategy
        status (LeaveStatus): Current status
        
        replacement_faculty_id (int): Replacement faculty (if strategy=REPLACEMENT)
        impact_analysis (dict): JSON with affected slots and proposals
        resolution_details (dict): JSON with applied changes
        
        reason (str): Leave reason/notes
        created_by (int): User who created leave record
    """
    __tablename__ = "faculty_leaves"
    
    # Core Fields
    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=False, index=True)
    timetable_id = Column(Integer, ForeignKey("timetables.id"), nullable=True)
    
    # Leave Period
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Leave Details
    leave_type = Column(String, nullable=False)
    strategy = Column(String, nullable=False, default=LeaveStrategy.WITHIN_SECTION_SWAP.value)
    status = Column(String, nullable=False, default=LeaveStatus.PROPOSED.value, index=True)
    
    # Resolution
    replacement_faculty_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Impact & Resolution Tracking (JSON)
    impact_analysis = Column(JSON, nullable=True)
    """
    Structure:
    {
        "affected_slots": [slot_id1, slot_id2, ...],
        "affected_sections": [section_id1, ...],
        "locked_slots": [slot_id1, ...],  // cross-dept, breaks
        "swap_proposals": [
            {
                "slot_id": 123,
                "current_faculty": "Dr. Smith",
                "proposed_faculty": "Dr. Jones",
                "same_section": true,
                "home_room": true,
                "granularity": "single_slot"
            }
        ],
        "total_impact": 15,
        "swappable_slots": 12,
        "locked_slots": 3
    }
    """
    
    resolution_details = Column(JSON, nullable=True)
    """
    Structure:
    {
        "applied_swaps": [
            {"slot_id": 123, "old_faculty": 5, "new_faculty": 8}
        ],
        "cancelled_slots": [slot_id1, ...],
        "timestamp": "2024-02-04T17:00:00Z"
    }
    """
    
    # Metadata
    reason = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    applied_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<FacultyLeave(id={self.id}, faculty={self.faculty_id}, status={self.status}, {self.start_date} to {self.end_date})>"
