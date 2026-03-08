"""
Tests for PreferenceWeightProvider
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.preference_weighting import PreferenceWeightProvider
from app.models.faculty import FacultyPreference


@pytest.mark.asyncio
async def test_build_weights_empty_db():
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)

    provider = PreferenceWeightProvider(mock_db)
    weights = await provider.build_weights()

    assert isinstance(weights, dict)
    assert len(weights) == 0


@pytest.mark.asyncio
async def test_build_weights_with_prefs():
    mock_pref = MagicMock(spec=FacultyPreference)
    mock_pref.faculty_id = 1
    mock_pref.day_of_week = 0
    mock_pref.time_slot_id = 2
    mock_pref.preference_type = 'preferred'

    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_pref]
    mock_db.execute = AsyncMock(return_value=mock_result)

    provider = PreferenceWeightProvider(mock_db)
    weights = await provider.build_weights()

    assert weights[(1, 0, 2)] == provider.pref_weight
