"""
Module: Faculty-Course Assignment
Repository: timeweaver_backend
Epic: 4 - Faculty Management & Workload

Defines the FacultyCourse model — the definitive "who teaches what to whom"
table: (faculty, course, section, semester).

Dependencies:
    - app.db.session (Base)
    - app.models.faculty (Faculty)
    - app.models.course (Course)
    - app.models.section (Section)
    - app.models.semester (Semester)
"""

from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.session import Base


class FacultyCourse(Base):
    """
    Assignment mapping: which faculty teaches which course to which section, per semester.

    This is the INPUT to timetable generation — the GA uses this to know
    who is teaching what, and only needs to figure out rooms + time slots.

    Attributes:
        id: Primary key
        faculty_id: FK to faculty table — the assigned instructor
        course_id: FK to courses table — the course being taught
        section_id: FK to sections table — the section being taught to
        semester_id: FK to semesters table — which semester this applies to
        is_primary: Whether this is the primary instructor (vs. co-instructor)
        created_at: Timestamp when assignment was created

    Relationships:
        faculty, course, section, semester
    """
    __tablename__ = "faculty_courses"

    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id = Column(Integer, ForeignKey("sections.id", ondelete="CASCADE"), nullable=False, index=True)
    semester_id = Column(Integer, ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False, index=True)
    is_primary = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint(
            "faculty_id", "course_id", "section_id", "semester_id",
            name="uq_faculty_course_section_semester"
        ),
    )

    # Relationships
    faculty = relationship("Faculty", back_populates="course_assignments")
    course = relationship("Course")
    section = relationship("Section")
    semester = relationship("Semester")
