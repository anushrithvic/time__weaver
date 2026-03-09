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
    
    def get_qualified_substitutes(
        self,
        course_id: int,
        department_id: int,
        original_faculty_id: int
    ) -> dict[int, str]:
        """
        Find faculty qualified to teach the course (they teach it in other sections),
        fallback to faculty in the same department.
        """
        from app.models.faculty_course import FacultyCourse
        from app.models.faculty import Faculty
        from app.models.user import User
        
        candidates = {}
        
        # Priority 1: Faculty already teaching this course to other sections
        stmt = select(FacultyCourse.faculty_id).where(
            FacultyCourse.course_id == course_id,
            FacultyCourse.faculty_id != original_faculty_id
        ).distinct()
        qualified_ids = [row[0] for row in self.db.execute(stmt)]
        
        # Priority 2: Anyone in the same department
        if not qualified_ids:
            stmt2 = select(Faculty.id).where(
                Faculty.department_id == department_id,
                Faculty.id != original_faculty_id
            )
            qualified_ids = [row[0] for row in self.db.execute(stmt2)]
            
        # Get names for the candidates
        if qualified_ids:
            fac_stmt = select(Faculty.id, User.full_name).join(
                User, Faculty.user_id == User.id
            ).where(Faculty.id.in_(qualified_ids))
            
            for fac_id, name in self.db.execute(fac_stmt):
                candidates[fac_id] = name
                
        return candidates

    def check_faculty_availability(
        self,
        faculty_id: int,
        timetable_id: int,
        day_of_week: int,
        start_slot_id: int,
        duration_slots: int
    ) -> bool:
        """Check if a faculty member is free during a specific time block."""
        # Check all slots they are assigned to
        stmt = select(TimetableSlot).where(
            TimetableSlot.timetable_id == timetable_id,
            TimetableSlot.primary_faculty_id == faculty_id,
            TimetableSlot.day_of_week == day_of_week
        )
        
        slots = self.db.execute(stmt).scalars().all()
        
        for slot in slots:
            # Check for overlap
            slot_end = slot.start_slot_id + slot.duration_slots
            req_end = start_slot_id + duration_slots
            
            if not (start_slot_id >= slot_end or req_end <= slot.start_slot_id):
                return False  # Overlap found
                
        return True

    def propose_within_section_swaps(
        self,
        affected_slots: list[TimetableSlot],
        locked_slot_ids: list[int],
        granularity: str = "single_slot"
    ) -> list[dict]:
        """
        Propose faculty swaps based on subject qualification and availability.
        """
        proposals = []
        
        for slot in affected_slots:
            if slot.id in locked_slot_ids:
                continue
            
            # Identify department
            section = self.db.get(Section, slot.section_id)
            if not section:
                continue
                
            # Get qualified candidates (taught this course or in same Dept)
            candidates = self.get_qualified_substitutes(
                slot.course_id, 
                section.department_id, 
                slot.primary_faculty_id
            )
            
            if not candidates:
                proposals.append({
                    "slot_id": slot.id,
                    "problem": "no_faculty_available",
                    "recommendation": "CANCELLATION"
                })
                continue
            
            home_room_id = section.dedicated_room_id
            found_sub = False
            
            for faculty_id, faculty_name in candidates.items():
                # Verify they are actually free during this time
                is_free = self.check_faculty_availability(
                    faculty_id, 
                    slot.timetable_id, 
                    slot.day_of_week, 
                    slot.start_slot_id, 
                    slot.duration_slots
                )
                
                if is_free:
                    proposal = {
                        "slot_id": slot.id,
                        "day": slot.day_of_week,
                        "start_slot": slot.start_slot_id,
                        "duration": slot.duration_slots,
                        "current_faculty_id": slot.primary_faculty_id,
                        "proposed_faculty_id": faculty_id,
                        "proposed_faculty_name": faculty_name,
                        "same_section": False, 
                        "home_room_match": (slot.room_id == home_room_id) if home_room_id else False,
                        "current_room_id": slot.room_id,
                        "granularity": granularity,
                        "priority": "high"
                    }
                    proposals.append(proposal)
                    found_sub = True
                    break  # Found best substitute for this slot
                    
            if not found_sub:
                proposals.append({
                    "slot_id": slot.id,
                    "problem": "candidates_busy",
                    "recommendation": "CANCELLATION"
                })
        
        # Sort by priority
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
