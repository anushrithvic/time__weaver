"""
Substitute Recommender Service
app.services.substitute_recommender

Provides candidate ranking for substitute assignments based on availability,
workload and simple suitability heuristics.

Owner: Meka Jahnavi
Epic: 2.6 - Substitute recommendation
"""

from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.faculty import Faculty, FacultyPreference
from app.services.workload_calculator import WorkloadCalculator


class SubstituteRecommender:
    """
    Rank eligible faculty for substitution.

    Simple scoring heuristic (configurable later):
      score = availability_score (0/1) * 100
            + (1 - utilization/100) * 50
            + dept_match * 25
            - 10 * recent_sub_count

    Higher score is better. Not-available faculty get filtered out.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def rank_candidates(
        self,
        semester_id: int,
        day: int,
        time_slot_id: int,
        department_id: Optional[int] = None,
        exclude_ids: Optional[List[int]] = None,
        top_n: int = 5
    ) -> List[Dict]:
        """
        Return top-N candidate dicts:
        {candidate_id, score, reason}
        """
        exclude_ids = exclude_ids or []

        # Load faculty optionally in same department
        query = select(Faculty)
        result = await self.db.execute(query)
        all_faculty = result.scalars().all()

        candidates = []

        for f in all_faculty:
            if f.id in exclude_ids:
                continue
            if department_id and f.department_id != department_id:
                # keep cross-department faculty but penalize later
                dept_match = 0
            else:
                dept_match = 1

            # Check availability: is there a 'not_available' preference for this slot?
            pref_q = select(FacultyPreference).where(
                and_(
                    FacultyPreference.faculty_id == f.id,
                    FacultyPreference.day_of_week == day,
                    FacultyPreference.time_slot_id == time_slot_id
                )
            )
            pref_res = await self.db.execute(pref_q)
            pref = pref_res.scalar_one_or_none()
            if pref and pref.preference_type == 'not_available':
                # Skip this candidate
                continue

            # Compute workload utilization (safe to call service)
            try:
                wl = await WorkloadCalculator.calculate_workload(f.id, semester_id, self.db)
                utilization = wl.get('utilization_percentage', 0.0)
            except Exception:
                utilization = 0.0

            # Recent substitution count: placeholder (0) - can be implemented using audit logs
            recent_sub_count = 0

            availability_score = 1  # available

            score = (
                availability_score * 100
                + (1 - utilization / 100.0) * 50
                + dept_match * 25
                - recent_sub_count * 10
            )

            reason = []
            if dept_match:
                reason.append('same department')
            else:
                reason.append('cross-department')
            reason.append(f'low utilization' if utilization < 50 else 'high utilization')

            candidates.append({
                'candidate_id': f.id,
                'score': round(score, 2),
                'utilization': round(utilization, 2),
                'reason': ', '.join(reason)
            })

        # Sort descending by score and return top_n
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates[:top_n]


__all__ = ["SubstituteRecommender"]
