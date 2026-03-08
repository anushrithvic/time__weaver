"""
Module: Timetable Generation & Scheduling (Module 3)
Repository: timeweaver_backend
Owner: Pranathi Nibhanipudi
Epic: 3 - Timetable Generation / Re-generation

Slot Locking Service - User Story 3.2

Handles locking and unlocking of timetable slots to protect critical
assignments during re-optimization and incremental updates.

Locked slots are:
- Protected from modification during generation
- Preserved during re-optimization
- Used for manual overrides and fixes

Dependencies:
    - app.models.timetable (TimetableSlot model)

User Stories: 3.2.2 (Slot Locking)
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.timetable import TimetableSlot, Timetable


class SlotLockingService:
    """Service for slot locking operations (async API-compatible)"""
    
    def __init__(self, db: AsyncSession):
        """Initialize with async database session"""
        self.db = db
    
    async def lock_slots(self, timetable_id: int, slot_ids: list[int]) -> dict:
        """
        Lock specified timetable slots.
        
        Args:
            timetable_id: Timetable ID
            slot_ids: List of slot IDs to lock
            
        Returns:
            Dict with locked_count and slot_ids
            
        Raises:
            ValueError: If timetable not found
        """
        # Verify timetable exists
        tt_query = select(Timetable).where(Timetable.id == timetable_id)
        tt_result = await self.db.execute(tt_query)
        if not tt_result.scalar_one_or_none():
            raise ValueError(f"Timetable {timetable_id} not found")
        
        stmt = (
            update(TimetableSlot)
            .where(
                TimetableSlot.timetable_id == timetable_id,
                TimetableSlot.id.in_(slot_ids)
            )
            .values(is_locked=True)
        )
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return {
            "locked_count": result.rowcount,
            "slot_ids": slot_ids
        }
    
    async def unlock_slots(self, timetable_id: int, slot_ids: list[int]) -> dict:
        """
        Unlock specified timetable slots.
        
        Args:
            timetable_id: Timetable ID
            slot_ids: List of slot IDs to unlock
            
        Returns:
            Dict with unlocked_count and slot_ids
            
        Raises:
            ValueError: If timetable not found
        """
        # Verify timetable exists
        tt_query = select(Timetable).where(Timetable.id == timetable_id)
        tt_result = await self.db.execute(tt_query)
        if not tt_result.scalar_one_or_none():
            raise ValueError(f"Timetable {timetable_id} not found")
        
        stmt = (
            update(TimetableSlot)
            .where(
                TimetableSlot.timetable_id == timetable_id,
                TimetableSlot.id.in_(slot_ids)
            )
            .values(is_locked=False)
        )
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return {
            "unlocked_count": result.rowcount,
            "slot_ids": slot_ids
        }
    
    async def get_locked_slots(self, timetable_id: int) -> dict:
        """
        Get all locked slots for a timetable.
        
        Args:
            timetable_id: Timetable ID
            
        Returns:
            Dict with locked_slots list and total_locked count
            
        Raises:
            ValueError: If timetable not found
        """
        # Verify timetable exists
        tt_query = select(Timetable).where(Timetable.id == timetable_id)
        tt_result = await self.db.execute(tt_query)
        if not tt_result.scalar_one_or_none():
            raise ValueError(f"Timetable {timetable_id} not found")
        
        stmt = select(TimetableSlot).where(
            TimetableSlot.timetable_id == timetable_id,
            TimetableSlot.is_locked == True
        )
        
        result = await self.db.execute(stmt)
        slots = list(result.scalars().all())
        
        return {
            "locked_slots": slots,
            "total_locked": len(slots)
        }
    
    async def lock_all_slots_for_timetable(self, timetable_id: int) -> int:
        """
        Lock ALL slots in a timetable (for publishing).
        
        Args:
            timetable_id: Timetable ID
            
        Returns:
            Number of slots locked
        """
        stmt = (
            update(TimetableSlot)
            .where(TimetableSlot.timetable_id == timetable_id)
            .values(is_locked=True)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount
    
    async def unlock_all_slots_for_timetable(self, timetable_id: int) -> int:
        """
        Unlock ALL slots in a timetable (for re-generation).
        
        Args:
            timetable_id: Timetable ID
            
        Returns:
            Number of slots unlocked
        """
        stmt = (
            update(TimetableSlot)
            .where(TimetableSlot.timetable_id == timetable_id)
            .values(is_locked=False)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount
    
    async def get_lock_statistics(self, timetable_id: int) -> dict:
        """
        Get locking statistics for a timetable.
        
        Args:
            timetable_id: Timetable ID
            
        Returns:
            Dict with lock statistics
        """
        stmt = select(TimetableSlot).where(TimetableSlot.timetable_id == timetable_id)
        result = await self.db.execute(stmt)
        all_slots = list(result.scalars().all())
        
        locked_count = sum(1 for slot in all_slots if slot.is_locked)
        unlocked_count = len(all_slots) - locked_count
        
        return {
            "total_slots": len(all_slots),
            "locked_slots": locked_count,
            "unlocked_slots": unlocked_count,
            "lock_percentage": (locked_count / len(all_slots) * 100) if all_slots else 0
        }
