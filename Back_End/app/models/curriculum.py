"""
Curriculum and Elective Assignment Models

This module defines new models for Epic 3 backend implementation:
1. Curriculum - Maps courses to (department, year_level, semester_type)
2. CourseElectiveAssignment - Maps elective courses to groups per semester
3. CourseBatchingConfig - Lab batching configuration per course/semester

Epic 3: User Stories 3.1-3.8
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, UniqueConstraint, ARRAY, CheckConstraint, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.semester import SemesterType


class Curriculum(Base):
    """
    Curriculum model - maps which courses are taught in each (department, year, semester_type).
    
    This model simplifies curriculum management by using year_level (1-4) and semester_type (ODD/EVEN)
    instead of specific semester numbers. All metadata (hours, category) is read from the Course table.
    
    Attributes:
        id (int): Primary key
        department_id (int): Foreign key to departments
        year_level (int): Academic year level (1-4)
        semester_type (SemesterType): ODD or EVEN semester
        course_id (int): Foreign key to courses
        is_mandatory (bool): True for CORE courses, False for electives
        created_at (datetime): Timestamp when created
    
    Example:
        # CSE Year 3 ODD Semester Curriculum
        Curriculum(dept_id=1, year_level=3, semester_type='ODD', course_id=101, is_mandatory=True)
        Curriculum(dept_id=1, year_level=3, semester_type='ODD', course_id=201, is_mandatory=False)  # PE1
    """
    __tablename__ = "curriculum"
    
    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, index=True)
    year_level = Column(Integer, nullable=False)  # 1, 2, 3, or 4
    semester_type = Column(String, nullable=False)  # ODD or EVEN
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    is_mandatory = Column(Boolean, nullable=False, default=True)  # CORE=True, Elective=False
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('department_id', 'year_level', 'semester_type', 'course_id', 
                        name='uq_curriculum_dept_year_sem_course'),
        CheckConstraint('year_level >= 1 AND year_level <= 4', name='check_year_level_valid'),
    )
    
    def __repr__(self):
        return f"<Curriculum(dept={self.department_id}, year={self.year_level}, sem={self.semester_type}, course={self.course_id})>"


class CourseElectiveAssignment(Base):
    """
    CourseElectiveAssignment model - maps which courses are offered in each elective group per semester.
    
    This separates permanent elective groups (PE1, PE2, FE1) from per-semester course assignments.
    Includes assigned_room_id for PE courses that need fixed rooms throughout the semester.
    
    Attributes:
        id (int): Primary key
        elective_group_id (int): Foreign key to elective_groups (permanent)
        semester_id (int): Foreign key to semesters (which semester)
        course_id (int): Foreign key to courses (which PE/FE course)
        assigned_room_id (int): Foreign key to rooms (pre-assigned room for PE)
        created_at (datetime): Timestamp when created
    
    Example:
        # Semester 5, PE1 offerings
        CourseElectiveAssignment(group_id=1, semester_id=5, course_id=201, room_id=101)  # Cryptography → ABIII-A205
        CourseElectiveAssignment(group_id=1, semester_id=5, course_id=202, room_id=102)  # AI → ABIII-C205
    """
    __tablename__ = "course_elective_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    elective_group_id = Column(Integer, ForeignKey("elective_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    semester_id = Column(Integer, ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_room_id = Column(Integer, ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True)  # Pre-assigned room for PE
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('elective_group_id', 'semester_id', 'course_id', 
                        name='uq_elective_assignment_group_sem_course'),
    )
    
    def __repr__(self):
        return f"<CourseElectiveAssignment(group={self.elective_group_id}, sem={self.semester_id}, course={self.course_id})>"


class CourseBatchingConfig(Base):
    """
    CourseBatchingConfig model - configuration for lab course batching per semester.
    
    Admin-configured institutional rules defining how many batches a lab course should
    be divided into and the batch size. Applied during timetable generation.
    
    Attributes:
        id (int): Primary key
        course_id (int): Foreign key to courses (must be a lab course)
        semester_id (int): Foreign key to semesters
        num_batches (int): Number of batches to create (1-10)
        batch_size (int): Students per batch
        created_at (datetime): Timestamp when created
    
    Example:
        # Machine Learning Lab: Split 60 students into 2 batches of 30
        CourseBatchingConfig(course_id=101, semester_id=5, num_batches=2, batch_size=30)
    """
    __tablename__ = "course_batching_config"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    semester_id = Column(Integer, ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False, index=True)
    num_batches = Column(Integer, nullable=False)
    batch_size = Column(Integer, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('course_id', 'semester_id', name='uq_batching_course_sem'),
        CheckConstraint('num_batches >= 1 AND num_batches <= 10', name='check_num_batches_valid'),
        CheckConstraint('batch_size > 0', name='check_batch_size_positive'),
    )
    
    def __repr__(self):
        return f"<CourseBatchingConfig(course={self.course_id}, sem={self.semester_id}, batches={self.num_batches})>"
