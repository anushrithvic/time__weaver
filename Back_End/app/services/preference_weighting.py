"""
Preference Weight Provider
app.services.preference_weighting

Provides a mapping from faculty/time-slot preferences to numeric weights
used by the timetable generator's fitness function.

Owner: Meka Jahnavi
Epic: 2 - Faculty Profile, Availability & Preference
"""

import os
from typing import Dict, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.faculty import FacultyPreference


class PreferenceWeightProvider:
    """
    Build a weight map for preferences.

    Returns a dict keyed by (faculty_id, day_of_week, time_slot_id) -> weight (float).
    Configuration via environment variables:
      - PREFERENCE_SOFT ("true"|"false") default true
      - PREF_WEIGHT (float) default 1.0
      - NOT_AVAILABLE_WEIGHT (float) default -9999
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.soft = os.getenv("PREFERENCE_SOFT", "true").lower() == "true"
        self.pref_weight = float(os.getenv("PREF_WEIGHT", "1.0"))
        self.not_available_weight = float(os.getenv("NOT_AVAILABLE_WEIGHT", "-9999"))

    async def build_weights(self, semester_id: int = None) -> Dict[Tuple[int, int, int], float]:
        """
        Query `FacultyPreference` table and produce weight mapping.

        Args:
            semester_id: optional, reserved for future filtering if preferences become semester-scoped

        Returns:
            dict: {(faculty_id, day_of_week, time_slot_id): weight}
        """
        query = select(FacultyPreference)
        result = await self.db.execute(query)
        prefs = result.scalars().all()

        weight_map: Dict[Tuple[int, int, int], float] = {}

        for p in prefs:
            key = (p.faculty_id, p.day_of_week, p.time_slot_id)
            if p.preference_type == "preferred":
                weight = self.pref_weight
            elif p.preference_type == "not_available":
                weight = self.not_available_weight
            else:
                # Unknown preference type - ignore (weight 0)
                weight = 0.0

            weight_map[key] = weight

        return weight_map


__all__ = ["PreferenceWeightProvider"]
