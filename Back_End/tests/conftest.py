"""
Pytest configuration and shared fixtures for automated tests.
"""

import os
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.db.session import get_db, Base
from app.core.config import settings
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from sqlalchemy import select
# Import base to register all models with SQLAlchemy
from app.db import base


# ============================================================================
# ASYNC EVENT LOOP CONFIGURATION
# ============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.
    
    Ensures tables are created for the test session.
    Uses 'timeweaver_test' database instead of production database.
    """
    # Use TEST_DATABASE_URL from environment (never hardcode credentials)
    test_database_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://postgres:your_password_here@localhost:5432/timeweaver_test"
    )
    
    # Disable statement cache to prevent InvalidCachedStatementError when schemas are recreated
    engine = create_async_engine(
        test_database_url, 
        echo=False,
        connect_args={"statement_cache_size": 0}
    )
    
    # Create tables (ensure Enums and schema exist)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def setup_admin(test_db: AsyncSession):
    """Ensure admin user exists for tests"""
    # Check if admin exists
    result = await test_db.execute(select(User).where(User.username == "admin"))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True,
            is_superuser=True,
            full_name="Admin User"
        )
        test_db.add(user)
        # Commit to make visible to other sessions (e.g. client API calls)
        await test_db.commit()
        await test_db.refresh(user)
    return user


# ============================================================================
# CLIENT FIXTURES
# ============================================================================

@pytest.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing"""
    
    # Override get_db dependency to use the test database session
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    
    # Store original middleware
    original_middleware = app.user_middleware.copy()
    
    # Filter out AuditLoggingMiddleware to prevent BaseHTTPMiddleware/anyio conflicts during tests
    # This is necessary because BaseHTTPMiddleware has known issues with TaskGroups in tests
    app.user_middleware = [
        m for m in app.user_middleware 
        if m.cls.__name__ != "AuditLoggingMiddleware"
    ]
    
    # Rebuild the middleware stack to apply changes
    app.middleware_stack = app.build_middleware_stack()
    
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            follow_redirects=False
        ) as ac:
            yield ac
            
    finally:
        # Restore original middleware stack
        app.user_middleware = original_middleware
        app.middleware_stack = app.build_middleware_stack()
        # Clear dependency overrides
        app.dependency_overrides.clear()


# ============================================================================
# AUTHENTICATION FIXTURES
# ============================================================================

@pytest.fixture
async def admin_token(client: AsyncClient, setup_admin):
    """Get admin authentication token"""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(admin_token: str) -> dict:
    """Get authorization headers with admin token"""
    return {"Authorization": f"Bearer {admin_token}"}


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_rule_data() -> dict:
    """Sample institutional rule data for testing"""
    return {
        "name": "Test Rule",
        "description": "Test rule for automated testing",
        "rule_type": "TIME_WINDOW",
        "configuration": {"min_slot": 2, "max_slot": 8},
        "is_hard_constraint": True,
        "weight": 1.0,
        "applies_to_departments": [],
        "applies_to_years": [],
        "is_active": True
    }


@pytest.fixture
def sample_timetable_gen_data() -> dict:
    """Sample timetable generation request data"""
    return {
        "semester_id": 1,
        "algorithm": "GA",
        "num_solutions": 3,
        "max_generations": 50,
        "population_size": 20,
        "mutation_rate": 0.1
    }


@pytest.fixture
def sample_leave_data() -> dict:
    """Sample faculty leave data"""
    return {
        "faculty_id": 1,
        "semester_id": 1,
        "timetable_id": 1,
        "start_date": "2024-10-01",
        "end_date": "2024-10-07",
        "leave_type": "SICK",
        "strategy": "WITHIN_SECTION_SWAP",
        "reason": "Medical emergency"
    }


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================


# ============================================================================
# MODEL FIXTURES
# ============================================================================

@pytest.fixture
async def sample_admin_user(test_db: AsyncSession, setup_admin):
   """Get the admin user model instance"""
   return setup_admin

@pytest.fixture
async def sample_semester(test_db: AsyncSession) -> "Semester":
    from app.models.semester import Semester, SemesterType
    from datetime import date
    sem = Semester(
        name="Fall 2024",
        start_date=date(2024, 8, 1),
        end_date=date(2024, 12, 15),
        semester_type=SemesterType.ODD
    )
    test_db.add(sem)
    await test_db.commit()
    await test_db.refresh(sem)
    return sem

@pytest.fixture
async def sample_timetable(test_db: AsyncSession, sample_semester, sample_admin_user) -> "Timetable":
    from app.models.timetable import Timetable
    tt = Timetable(
        semester_id=sample_semester.id,
        name="Test Timetable",
        status="generating",
        created_by_user_id=sample_admin_user.id
    )
    test_db.add(tt)
    await test_db.commit()
    await test_db.refresh(tt)
    return tt

@pytest.fixture
async def sample_rooms(test_db: AsyncSession) -> list:
    from app.models.room import Room
    rooms = [
        Room(name="101", capacity=50, building="Bio Block"),
        Room(name="102", capacity=30, building="Bio Block")
    ]
    test_db.add_all(rooms)
    await test_db.commit()
    for r in rooms: await test_db.refresh(r)
    return rooms

@pytest.fixture
async def sample_time_slots(test_db: AsyncSession) -> list:
    from app.models.time_slot import TimeSlot
    from datetime import time
    slots = [
        TimeSlot(start_time=time(9,0), end_time=time(10,0)),
        TimeSlot(start_time=time(10,0), end_time=time(11,0))
    ]
    test_db.add_all(slots)
    await test_db.commit()
    for s in slots: await test_db.refresh(s)
    return slots

@pytest.fixture
async def sample_sections(test_db: AsyncSession, sample_semester) -> list:
    # Need a course first
    from app.models.course import Course, CourseCategory
    from app.models.section import Section
    
    c = Course(code="CS101", name="Intro to CS", credits=3, category=CourseCategory.CORE)
    test_db.add(c)
    await test_db.commit()
    
    sections = [
        Section(name="A", semester_id=sample_semester.id, course_id=c.id, student_count=40)
    ]
    test_db.add_all(sections)
    await test_db.commit()
    for s in sections: await test_db.refresh(s)
    return sections

@pytest.fixture(autouse=True)
async def cleanup_test_data():
    """
    Cleanup test data after each test.
    """
    yield
    # Cleanup handled by rollback transaction strategy in test_db fixture usually,
    # but since we are not using that strategy (test_db yields session then rollbacks), it works.
    pass
