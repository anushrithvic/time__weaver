"""
Tests for SubstituteRecommender
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.substitute_recommender import SubstituteRecommender


@pytest.mark.asyncio
async def test_rank_candidates_empty_db():
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)

    recommender = SubstituteRecommender(mock_db)
    candidates = await recommender.rank_candidates(semester_id=1, day=0, time_slot_id=1)

    assert isinstance(candidates, list)
    assert len(candidates) == 0


@pytest.mark.asyncio
async def test_rank_candidates_filters_unavailable():
    # This test will mock one faculty and a not_available preference to ensure filtering
    mock_faculty = MagicMock()
    mock_faculty.id = 1
    mock_faculty.department_id = 1

    mock_pref = MagicMock()
    mock_pref.faculty_id = 1
    mock_pref.day_of_week = 0
    mock_pref.time_slot_id = 1
    mock_pref.preference_type = 'not_available'

    # Mock DB execute for faculty list
    mock_db = AsyncMock(spec=AsyncSession)
    faculty_result = MagicMock()
    faculty_result.scalars.return_value.all.return_value = [mock_faculty]
    
    # Mock the preference query result
    pref_result = MagicMock()
    pref_result.scalar_one_or_none.return_value = mock_pref
    
    mock_db.execute = AsyncMock(side_effect=[faculty_result, pref_result])

    recommender = SubstituteRecommender(mock_db)
    candidates = await recommender.rank_candidates(semester_id=1, day=0, time_slot_id=1)

    # Candidate with not_available should be filtered out => empty list
    assert candidates == []
