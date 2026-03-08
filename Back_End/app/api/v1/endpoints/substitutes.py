"""
Substitutes API endpoints
GET /api/v1/substitutes -> rank candidates
POST /api/v1/substitutes/assign -> assign substitute to section/slot

Owner: Meka Jahnavi
Epic: 2.6 - Substitute recommendation
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.core.dependencies import get_current_admin, get_current_user
from app.services.substitute_recommender import SubstituteRecommender
from app.models.section import Section
from app.models.faculty import Faculty

router = APIRouter()


@router.get("/")
async def get_substitute_candidates(
    day: int,
    time_slot_id: int,
    semester_id: int,
    department_id: int = None,
    exclude: str = "",
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    """Return ranked substitute candidates for a slot.

    Query params:
      - day, time_slot_id, semester_id
      - department_id (optional)
      - exclude (comma-separated faculty ids)
    """
    exclude_ids = [int(x) for x in exclude.split(",") if x.strip().isdigit()]

    recommender = SubstituteRecommender(db)
    candidates = await recommender.rank_candidates(
        semester_id=semester_id,
        day=day,
        time_slot_id=time_slot_id,
        department_id=department_id,
        exclude_ids=exclude_ids,
        top_n=10
    )
    return candidates


@router.post("/assign", status_code=status.HTTP_200_OK)
async def assign_substitute(
    section_id: int,
    substitute_id: int,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """Assign a substitute teacher to a section (admin only).

    This is a minimal implementation that reassigns `section.faculty_id`.
    In a real system we would create a substitution record and notify parties.
    """
    section = await db.get(Section, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    # Verify substitute exists
    substitute = await db.get(Faculty, substitute_id)
    if not substitute:
        raise HTTPException(status_code=404, detail="Substitute faculty not found")

    # Assign
    section.faculty_id = substitute_id
    db.add(section)
    await db.commit()
    await db.refresh(section)

    return {"status": "assigned", "section_id": section_id, "substitute_id": substitute_id}
