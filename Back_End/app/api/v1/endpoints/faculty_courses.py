"""
Module: Faculty-Course Assignment
Repository: timeweaver_backend
Epic: 4 - Faculty Management & Workload

Faculty-Course Assignment API endpoints for CRUD operations.
Manages which faculty teaches which course to which section per semester.

Dependencies:
    - app.models.faculty_course (FacultyCourse model)
    - app.models.faculty (Faculty model)
    - app.models.course (Course model)
    - app.models.section (Section model)
    - app.models.semester (Semester model)
    - app.schemas.faculty_course (Pydantic schemas)
    - app.core.dependencies (get_current_admin)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.db.session import get_db
from app.models.user import User
from app.models.faculty import Faculty
from app.models.faculty_course import FacultyCourse
from app.models.course import Course
from app.models.section import Section
from app.models.semester import Semester
from app.schemas.faculty_course import (
    FacultyCourseCreate, FacultyCourseUpdate,
    FacultyCourseResponse, FacultyCourseDetail
)
from app.core.dependencies import get_current_admin


router = APIRouter()


# ── Helpers ─────────────────────────────────────────────────────

async def _build_detail(fc: FacultyCourse, db: AsyncSession) -> FacultyCourseDetail:
    """Enrich a FacultyCourse row with names for display."""
    faculty = await db.get(Faculty, fc.faculty_id)
    course = await db.get(Course, fc.course_id)
    section = await db.get(Section, fc.section_id)
    semester = await db.get(Semester, fc.semester_id)

    # Get faculty's full_name from linked User
    faculty_name = None
    if faculty:
        user = await db.get(User, faculty.user_id)
        faculty_name = user.full_name if user else None

    return FacultyCourseDetail(
        id=fc.id,
        faculty_id=fc.faculty_id,
        faculty_name=faculty_name,
        employee_id=faculty.employee_id if faculty else None,
        course_id=fc.course_id,
        course_code=course.code if course else None,
        course_name=course.name if course else None,
        section_id=fc.section_id,
        section_name=section.name if section else None,
        semester_id=fc.semester_id,
        semester_name=semester.name if semester else None,
        is_primary=fc.is_primary,
        created_at=fc.created_at,
    )


# ── Endpoints ───────────────────────────────────────────────────

@router.post("/", response_model=FacultyCourseResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    data: FacultyCourseCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """
    Assign a faculty member to teach a course for a specific section & semester.

    **Admin only.**
    """
    # Validate all FKs exist
    if not await db.get(Faculty, data.faculty_id):
        raise HTTPException(status_code=404, detail="Faculty not found")
    if not await db.get(Course, data.course_id):
        raise HTTPException(status_code=404, detail="Course not found")
    if not await db.get(Section, data.section_id):
        raise HTTPException(status_code=404, detail="Section not found")
    if not await db.get(Semester, data.semester_id):
        raise HTTPException(status_code=404, detail="Semester not found")

    # Check for duplicate
    existing = await db.execute(
        select(FacultyCourse).where(
            FacultyCourse.faculty_id == data.faculty_id,
            FacultyCourse.course_id == data.course_id,
            FacultyCourse.section_id == data.section_id,
            FacultyCourse.semester_id == data.semester_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="This faculty is already assigned to this course/section/semester"
        )

    fc = FacultyCourse(**data.model_dump())
    db.add(fc)
    await db.commit()
    await db.refresh(fc)
    return fc


@router.get("/", response_model=list[FacultyCourseDetail])
async def list_assignments(
    semester_id: Optional[int] = Query(None, description="Filter by semester"),
    faculty_id: Optional[int] = Query(None, description="Filter by faculty"),
    course_id: Optional[int] = Query(None, description="Filter by course"),
    section_id: Optional[int] = Query(None, description="Filter by section"),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """
    List faculty-course assignments with optional filters.

    **Admin only.**
    """
    query = select(FacultyCourse)
    if semester_id:
        query = query.where(FacultyCourse.semester_id == semester_id)
    if faculty_id:
        query = query.where(FacultyCourse.faculty_id == faculty_id)
    if course_id:
        query = query.where(FacultyCourse.course_id == course_id)
    if section_id:
        query = query.where(FacultyCourse.section_id == section_id)

    result = await db.execute(query)
    rows = result.scalars().all()
    return [await _build_detail(fc, db) for fc in rows]


@router.get("/{assignment_id}", response_model=FacultyCourseDetail)
async def get_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Get a specific assignment by ID. **Admin only.**"""
    fc = await db.get(FacultyCourse, assignment_id)
    if not fc:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return await _build_detail(fc, db)


@router.put("/{assignment_id}", response_model=FacultyCourseResponse)
async def update_assignment(
    assignment_id: int,
    data: FacultyCourseUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Update an assignment (e.g. toggle is_primary). **Admin only.**"""
    fc = await db.get(FacultyCourse, assignment_id)
    if not fc:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if data.is_primary is not None:
        fc.is_primary = data.is_primary

    await db.commit()
    await db.refresh(fc)
    return fc


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Remove a faculty-course assignment. **Admin only.**"""
    fc = await db.get(FacultyCourse, assignment_id)
    if not fc:
        raise HTTPException(status_code=404, detail="Assignment not found")

    await db.delete(fc)
    await db.commit()
