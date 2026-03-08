"""
Course and Elective Group Database Models

This module defines two related SQLAlchemy models for academic course management:
1. ElectiveGroup - Groups of optional courses students can choose from
2. Course - Individual courses with theory/lab hour specifications

Epic 1: User Stories 1.4 and 1.5
- User Story 1.4: Define course details (theory hours, lab hours, credits)
- User Story 1.5: Define elective groups for student choice

Database Tables: elective_groups, courses

Relationships:
    - ElectiveGroup has many Courses (one-to-many)
    - Course belongs to one Department (many-to-one)
    - Course optionally belongs to one ElectiveGroup (many-to-one)
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, CheckConstraint, Enum as SQLEnum, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.db.session import Base


class CourseCategory(str, enum.Enum):
    """
    Course category enumeration for curriculum classification.
    
    Categories:
        CORE: Mandatory core courses for all students in a program
        PROFESSIONAL_ELECTIVE: Department-specific elective courses (PE1, PE2)
        FREE_ELECTIVE: Cross-department elective courses (FE1)
        PROJECT: Project-based courses (capstone projects)
        MENTORING: Mentoring/tutorial sessions
    """
    CORE = "CORE"
    PROFESSIONAL_ELECTIVE = "PROFESSIONAL_ELECTIVE"
    FREE_ELECTIVE = "FREE_ELECTIVE"
    PROJECT = "PROJECT"
    MENTORING = "MENTORING"


class ElectiveGroup(Base):
    """
    ElectiveGroup model representing a collection of elective courses.
    
    An elective group represents a permanent collection of elective slots (e.g., PE1, PE2, FE1).
    The actual courses offered change per semester via CourseElectiveAssignment.
    
    Attributes:
        id (int): Primary key, unique identifier
        name (str): Group name (e.g., "PE1", "PE2", "FE1-EVS")
        description (str): Optional detailed description
        participating_department_ids (list[int]): Array of department IDs that participate (for FE groups)
        created_at (datetime): Record creation timestamp
    
    Relationships:
        course_assignments: Per-semester course assignments via CourseElectiveAssignment
    
    Example:
        # PE1 for CSE and ECE departments
        group = ElectiveGroup(
            name="PE1",
            description="Professional Elective Group 1",
            participating_department_ids=[1, 2]  # CSE, ECE
        )
    """
    __tablename__ = "elective_groups"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Core Fields
    name = Column(String(100), nullable=False, unique=True)  # E.g., "PE1", "PE2", "FE1"
    description = Column(String, nullable=True)  # Optional detailed description
    
    # Cross-department participation (for FE groups)
    participating_department_ids = Column(ARRAY(Integer), default=list)  # E.g., [1, 2, 3] for CSE, ECE, MECH
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships: course_elective_assignments (per semester)
    
    def __repr__(self):
        """String representation for debugging."""
        return f"<ElectiveGroup(id={self.id}, name='{self.name}')>"


class Course(Base):
    """
    Course model representing an academic course with theory and lab components.
    
    Courses can be core (required) or elective (optional). They specify the number
    of theory hours, lab hours, tutorial hours, and total credits. Courses requiring 
    labs must be scheduled in lab-type rooms with appropriate equipment.
    
    Attributes:
        id (int): Primary key, unique identifier
        code (str): Unique course code (e.g., "CS301")
        name (str): Full course name
        theory_hours (int): Weekly theory lecture hours (0-10)
        lab_hours (int): Weekly lab practice hours (0-10)
        tutorial_hours (int): Weekly tutorial/discussion hours (0-10)
        credits (int): Academic credits awarded for completion
        department_id (int): Department offering this course
        is_elective (bool): True if course is elective, False if core/required
        elective_group_id (int): Optional foreign key if course is an elective
        requires_lab (bool): True if course needs lab facilities
        min_room_capacity (int): Minimum room capacity needed
        created_at (datetime): Record creation timestamp
    
    Constraints:
        - At least one of theory_hours, lab_hours, or tutorial_hours must be > 0
        - All hour fields must be >= 0
        - Credits must be > 0
        - Course code must be unique
    
    Relationships:
        department: The department offering this course
        elective_group: The elective group this course belongs to (if elective)
    
    Example:
        course = Course(
            code="CS301",
            name="Data Structures and Algorithms",
            theory_hours=3,
            lab_hours=2,
            tutorial_hours=1,
            credits=4,
            department_id=1,
            requires_lab=True,
            min_room_capacity=60
        )
    """
    __tablename__ = "courses"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Core Identification Fields
    code = Column(String(20), nullable=False, unique=True, index=True)  # E.g., "CS301"
    name = Column(String(200), nullable=False)  # Full course name
    
    # Course Structure Fields
    theory_hours = Column(Integer, default=0, nullable=False)  # Weekly theory hours
    lab_hours = Column(Integer, default=0, nullable=False)  # Weekly lab hours
    tutorial_hours = Column(Integer, default=0, nullable=False)  # Weekly tutorial hours
    credits = Column(Integer, nullable=False)  # Academic credits (typically 1-6)
    
    # Organizational Fields
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)  # Owning department
    course_category = Column(String, nullable=False, default=CourseCategory.CORE.value)  # Course type
    is_elective = Column(Boolean, default=False)  # DEPRECATED: use course_category instead
    elective_group_id = Column(Integer, ForeignKey("elective_groups.id"), nullable=True)  # Group if elective
    
    # Scheduling Requirements
    requires_lab = Column(Boolean, default=False)  # Needs lab facilities
    min_room_capacity = Column(Integer, nullable=True)  # Minimum seats required
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Database-level constraints to ensure data integrity
    # These are enforced by PostgreSQL
    __table_args__ = (
        CheckConstraint("theory_hours + lab_hours + tutorial_hours > 0", name="check_hours_positive"),
        CheckConstraint("theory_hours >= 0", name="check_theory_hours_nonnegative"),
        CheckConstraint("lab_hours >= 0", name="check_lab_hours_nonnegative"),
        CheckConstraint("tutorial_hours >= 0", name="check_tutorial_hours_nonnegative"),
        CheckConstraint("credits > 0", name="check_credits_positive"),
    )
    
    # Relationships (commented until circular imports resolved)
    # department = relationship("Department", back_populates="courses")
    # elective_group = relationship("ElectiveGroup", back_populates="courses")
    
    def __repr__(self):
        """String representation for debugging."""
        return f"<Course(id={self.id}, code='{self.code}', name='{self.name}')>"
