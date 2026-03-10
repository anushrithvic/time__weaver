"""
Module: Faculty Management & Workload
Repository: timeweaver_backend
Owner: Meka Jahnavi

Test suite for Faculty CRUD endpoints and models.
Uses pytest for async integration testing against the test database.

Test Coverage: Faculty model, API endpoints, CRUD operations, Workload
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import status

from app.models.faculty import Faculty, FacultyPreference
from app.models.user import User, UserRole
from app.models.department import Department
from app.schemas.faculty import FacultyPreferenceCreate
from app.core.security import get_password_hash
import uuid

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
async def setup_department(test_db: AsyncSession):
    """Create a mock department for foreign key constraints."""
    # Generate unique code to prevent IntegrityError
    unique_code = f"CS_{uuid.uuid4().hex[:6]}" 
    dept = Department(name=f"Computer Science {unique_code}", code=unique_code)
    test_db.add(dept)
    await test_db.commit()
    await test_db.refresh(dept)
    return dept

@pytest.fixture
async def setup_faculty_user(test_db: AsyncSession):
    """Create a mock user with FACULTY role."""
    unique_id = uuid.uuid4().hex[:8]
    user = User(
        username=f"dr_smith_{unique_id}",
        email=f"smith_{unique_id}@example.com",
        hashed_password=get_password_hash("securepassword123"),
        role=UserRole.FACULTY,
        is_active=True,
        full_name="Dr. John Smith"
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user

@pytest.fixture
async def setup_faculty(test_db: AsyncSession, setup_faculty_user, setup_department):
    """Create a mock faculty profile attached to the user."""
    unique_emp_id = f"FAC_{uuid.uuid4().hex[:6]}"
    faculty = Faculty(
        user_id=setup_faculty_user.id,
        employee_id=unique_emp_id,
        department_id=setup_department.id,
        designation="Professor",
        max_hours_per_week=20
    )
    test_db.add(faculty)
    await test_db.commit()
    await test_db.refresh(faculty)
    return faculty


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_faculty_admin(client: AsyncClient, auth_headers: dict, setup_faculty_user, setup_department):
    """Test creating a new faculty profile as admin."""
    faculty_data = {
        "user_id": setup_faculty_user.id,
        "employee_id": "FAC002",
        "department_id": setup_department.id,
        "designation": "Associate Professor",
        "max_hours_per_week": 18
    }
    
    response = await client.post("/api/v1/faculty/", json=faculty_data, headers=auth_headers)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["employee_id"] == "FAC002"
    assert data["designation"] == "Associate Professor"
    assert "id" in data


@pytest.mark.asyncio
async def test_faculty_duplicate_user_id(client: AsyncClient, auth_headers: dict, setup_faculty, setup_department):
    """Test creating faculty with an already assigned user_id fails."""
    duplicate_data = {
        "user_id": setup_faculty.user_id, # Attempting to reuse existing user_id
        "employee_id": "FAC009",
        "department_id": setup_department.id
    }
    
    response = await client.post("/api/v1/faculty/", json=duplicate_data, headers=auth_headers)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_faculty_list(client: AsyncClient, auth_headers: dict, setup_faculty):
    """Test getting list of faculty as admin."""
    response = await client.get("/api/v1/faculty/", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 1
    assert any(f["employee_id"] == setup_faculty.employee_id for f in data)


@pytest.mark.asyncio
async def test_get_faculty_detail(client: AsyncClient, auth_headers: dict, setup_faculty):
    """Test getting detailed faculty info."""
    response = await client.get(f"/api/v1/faculty/{setup_faculty.id}", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == setup_faculty.id
    assert data["employee_id"] == setup_faculty.employee_id
    assert "preferences" in data  # Detail response should include preferences list


@pytest.mark.asyncio
async def test_update_faculty(client: AsyncClient, auth_headers: dict, setup_faculty, test_db: AsyncSession):
    """Test updating faculty profile."""
    update_data = {
        "designation": "Head of Department",
        "max_hours_per_week": 12
    }
    
    response = await client.put(f"/api/v1/faculty/{setup_faculty.id}", json=update_data, headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["designation"] == "Head of Department"
    assert data["max_hours_per_week"] == 12
    
    # Verify in DB
    await test_db.refresh(setup_faculty)
    assert setup_faculty.designation == "Head of Department"


@pytest.mark.asyncio
async def test_delete_faculty(client: AsyncClient, auth_headers: dict, setup_faculty, test_db: AsyncSession):
    """Test deleting faculty."""
    response = await client.delete(f"/api/v1/faculty/{setup_faculty.id}", headers=auth_headers)
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify deletion from DB
    result = await test_db.execute(select(Faculty).where(Faculty.id == setup_faculty.id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_faculty_authorization_checks(client: AsyncClient, setup_faculty):
    """Test RBAC for faculty endpoints (Unauthenticated)."""
    # Attempting to access without auth_headers should result in 401 Unauthorized
    response = await client.get("/api/v1/faculty/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    response = await client.delete(f"/api/v1/faculty/{setup_faculty.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_faculty_workload_not_found(client: AsyncClient, auth_headers: dict):
    """Test workload calculation for non-existent faculty."""
    response = await client.get("/api/v1/faculty/999/workload?semester_id=1", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# UNIT TESTS (Schemas & Models)
# ============================================================================

def test_faculty_model_creation():
    """Test basic Faculty model creation attributes."""
    faculty = Faculty(
        user_id=1,
        employee_id="FAC001",
        department_id=1,
        designation="Professor",
        max_hours_per_week=20
    )
    
    assert faculty.user_id == 1
    assert faculty.employee_id == "FAC001"
    assert faculty.max_hours_per_week == 20
    assert faculty.id is None  # Not persisted yet

def test_faculty_preference_validation():
    """Test FacultyPreferenceCreate validation logic."""
    # Valid preference
    valid = FacultyPreferenceCreate(day_of_week=0, time_slot_id=1, preference_type="not_available")
    assert valid.preference_type == "not_available"
    
    # Invalid preference type
    with pytest.raises(ValueError):
        FacultyPreferenceCreate(day_of_week=0, time_slot_id=1, preference_type="invalid_type")
        
    # Invalid day bounds
    with pytest.raises(ValueError):
        FacultyPreferenceCreate(day_of_week=8, time_slot_id=1, preference_type="preferred")