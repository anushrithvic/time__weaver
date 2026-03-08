"""
Module: Timetable Generation & Scheduling (Module 3)
Repository: timeweaver_backend
Owner: Pranathi Nibhanipudi
Epic: 3 - Timetable Generation / Re-generation

LeaveImpactAnalyzer Service

Analyzes the impact of faculty leave on timetables and proposes resolutions.
Identifies affected slots, locked slots (cross-dept, breaks), and suggests
within-section faculty swaps with home room preference.

Key Functions:
- find_affected_slots(faculty_id, timetable_id)
- identify_locked_slots(timetable_id) → cross-dept + breaks
- get_section_faculty(section_id) → faculty teaching that section
- propose_swaps() → suggest within-section swaps with home room priority
- analyze_leave_impact() → complete impact analysis for admin review

Dependencies:
    - app.models.faculty_leave (FacultyLeave)
    - app.models.timetable (TimetableSlot)
    - app.models.section (Section)
    - app.services.rule_engine (RuleEngine)

User Stories: 3.6, 3.8
"""

from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func
from typing import Optional
from datetime import date
from app.models.faculty_leave import FacultyLeave, LeaveStrategy
from app.models.timetable import TimetableSlot, Timetable
from app.models.section import Section
from app.models.course import Course
from app.models.time_slot import TimeSlot
from app.models.institutional_rule import InstitutionalRule, RuleType
from app.services.rule_engine import RuleEngine


class LeaveImpactAnalyzer:
    """Analyze faculty leave impact and propose resolutions"""
    
    def __init__(self, db: Session):
        """
        Initialize analyzer.
        
        Args:
            db: Database session
        """
        self.db = db
        self.rule_engine = RuleEngine()
    
    def find_affected_slots(
        self,
        faculty_id: int,
        timetable_id: int
    ) -> list[TimetableSlot]:
        """
        Find all slots where faculty is assigned.
        
        Args:
            faculty_id: Faculty member ID
            timetable_id: Timetable ID
            
        Returns:
            List of slots needing reassignment
        """
        slots = self.db.query(TimetableSlot).filter(
            TimetableSlot.timetable_id == timetable_id,
            or_(
                TimetableSlot.primary_faculty_id == faculty_id,
                TimetableSlot.assisting_faculty_ids.contains([faculty_id])
            )
        ).all()
        
        return slots
    
    def identify_locked_slots(self, timetable_id: int) -> list[int]:
        """
        Identify slots that cannot be modified.
        
        Locked if:
        1. Cross-department slots (same time, multiple departments)
        2. Break slots (TimeSlot.is_break = True)
        3. Violates SLOT_BLACKOUT rule
        
        Args:
            timetable_id: Timetable ID
            
        Returns:
            List of locked slot IDs
        """
        locked_slot_ids = []
        
        all_slots = self.db.query(TimetableSlot).filter(
            TimetableSlot.timetable_id == timetable_id
        ).all()
        
        # 1. Find cross-department slots
        # (same day + start_slot_id, multiple departments)
        time_groups = {}
        for slot in all_slots:
            key = (slot.day_of_week, slot.start_slot_id)
            if key not in time_groups:
                time_groups[key] = []
            time_groups[key].append(slot)
        
        for key, slots_at_time in time_groups.items():
            # Get departments for these slots
            departments = set()
            for slot in slots_at_time:
                section = self.db.get(Section, slot.section_id)
                if section:
                    departments.add(section.department_id)
            
            # If multiple departments → lock all these slots
            if len(departments) > 1:
                locked_slot_ids.extend([s.id for s in slots_at_time])
        
        # 2. Find break slots
        for slot in all_slots:
            # Check if time_slot is a break
            time_slot = self.db.query(TimeSlot).filter(
                TimeSlot.id == slot.start_slot_id
            ).first()
            
            if time_slot and time_slot.is_break:
                locked_slot_ids.append(slot.id)
        
        # 3. Check SLOT_BLACKOUT rules
        blackout_rules = self.db.query(InstitutionalRule).filter(
            InstitutionalRule.rule_type == RuleType.SLOT_BLACKOUT,
            InstitutionalRule.is_active == True
        ).all()
        
        for rule in blackout_rules:
            blackout_slots = rule.configuration.get("blackout_slots", [])
            for slot in all_slots:
                if slot.start_slot_id in blackout_slots:
                    locked_slot_ids.append(slot.id)
        
        return list(set(locked_slot_ids))  # Remove duplicates
    
    def get_section_faculty(
        self,
        section_id: int,
        timetable_id: int
    ) -> dict[int, str]:
        """
        Get all faculty teaching a particular section.
        
        Args:
            section_id: Section ID
            timetable_id: Timetable ID
            
        Returns:
            {faculty_id: faculty_name} for section
        """
        slots = self.db.query(TimetableSlot).filter(
            TimetableSlot.timetable_id == timetable_id,
            TimetableSlot.section_id == section_id,
            TimetableSlot.primary_faculty_id.isnot(None)
        ).all()
        
        faculty_map = {}
        for slot in slots:
            if slot.primary_faculty_id and slot.primary_faculty_id not in faculty_map:
                # Placeholder - in real app, query User model
                faculty_map[slot.primary_faculty_id] = f"Faculty-{slot.primary_faculty_id}"
        
        return faculty_map
    
    def propose_within_section_swaps(
        self,
        affected_slots: list[TimetableSlot],
        locked_slot_ids: list[int],
        granularity: str = "single_slot"
    ) -> list[dict]:
        """
        Propose faculty swaps within same section.
        
        Args:
            affected_slots: Slots needing reassignment
            locked_slot_ids: Slots that cannot be changed
            granularity: "single_slot", "same_day", "full_week", "admin_choice"
            
        Returns:
            List of swap proposals
        """
        proposals = []
        
        for slot in affected_slots:
            # Skip locked slots
            if slot.id in locked_slot_ids:
                continue
            
            # Get other faculty teaching this section
            section_faculty = self.get_section_faculty(slot.section_id, slot.timetable_id)
            
            # Remove the faculty on leave
            section_faculty.pop(slot.primary_faculty_id, None)
            
            if not section_faculty:
                # No faculty to swap with
                proposals.append({
                    "slot_id": slot.id,
                    "problem": "no_faculty_available",
                    "recommendation": "REPLACEMENT or REDISTRIBUTE"
                })
                continue
            
            # Get section details for home room check
            section = self.db.get(Section, slot.section_id)
            home_room_id = section.dedicated_room_id if section else None
            
            # Propose swaps with each available faculty
            for faculty_id, faculty_name in section_faculty.items():
                proposal = {
                    "slot_id": slot.id,
                    "day": slot.day_of_week,
                    "start_slot": slot.start_slot_id,
                    "duration": slot.duration_slots,
                    "current_faculty_id": slot.primary_faculty_id,
                    "proposed_faculty_id": faculty_id,
                    "proposed_faculty_name": faculty_name,
                    "same_section": True,
                    "home_room_match": (slot.room_id == home_room_id) if home_room_id else False,
                    "current_room_id": slot.room_id,
                    "granularity": granularity,
                    "priority": "high" if (slot.room_id == home_room_id) else "medium"
                }
                proposals.append(proposal)
                break  # Only first suggestion for now
        
        # Sort by priority (home room matches first)
        proposals.sort(key=lambda x: (
            x.get("priority") == "high",
            x.get("home_room_match", False)
        ), reverse=True)
        
        return proposals
    
    def analyze_leave_impact(
        self,
        leave: FacultyLeave
    ) -> dict:
        """
        Complete impact analysis for a faculty leave.
        
        Args:
            leave: FacultyLeave record
            
        Returns:
            Impact analysis dict to store in leave.impact_analysis
        """
        if not leave.timetable_id:
            return {
                "error": "No timetable assigned to semester"
            }
        
        # Find affected slots
        affected_slots = self.find_affected_slots(
            leave.faculty_id,
            leave.timetable_id
        )
        
        # Identify locked slots
        locked_slot_ids = self.identify_locked_slots(leave.timetable_id)
        
        # Get affected sections
        affected_section_ids = list(set([s.section_id for s in affected_slots]))
        
        # Propose swaps based on strategy
        swap_proposals = []
        if leave.strategy == LeaveStrategy.WITHIN_SECTION_SWAP:
            swap_proposals = self.propose_within_section_swaps(
                affected_slots,
                locked_slot_ids,
                granularity="admin_choice"  # Admin decides
            )
        
        # Count locked affected slots
        locked_affected = [s.id for s in affected_slots if s.id in locked_slot_ids]
        
        return {
            "affected_slots": [s.id for s in affected_slots],
            "affected_sections": affected_section_ids,
            "locked_slots": locked_slot_ids,
            "locked_affected_slots": locked_affected,
            "swap_proposals": swap_proposals,
            "total_impact": len(affected_slots),
            "swappable_slots": len(affected_slots) - len(locked_affected),
            "locked_count": len(locked_affected),
            "analysis_timestamp": str(date.today())
        }
