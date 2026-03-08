"""
Module: Faculty Management & Workload
Repository: timeweaver_backend
Owner: Meka Jahnavi
Epic: 4 - Faculty Management & Workload

This module defines Faculty and FacultyPreference database models.
Handles faculty profiles, preferences, and workload tracking.

Dependencies:
    - app.db.base_class (Base model)
    - app.models.user (User model)
    - app.models.department (Department model)
    - app.models.time_slots (TimeSlot model)
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.session import Base


class Faculty(Base):
    """
    Faculty model representing a teaching faculty member.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to users table (one-to-one)
        employee_id: Unique employee identifier
        department_id: Foreign key to departments table
        designation: Faculty designation (Professor, Assoc Prof, Lecturer, etc)
        max_hours_per_week: Maximum teaching hours per week (default 18)
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
        
    Relationships:
        user: Reference to User model
        department: Reference to Department model
        preferences: List of FacultyPreference records
    """
    __tablename__ = "faculty"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    employee_id = Column(String(20), unique=True, nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    designation = Column(String(50), default="Lecturer")  # Professor, Assoc Prof, Lecturer
    max_hours_per_week = Column(Integer, default=18)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
    # Relationships
    user = relationship("User", back_populates="faculty")
    department = relationship("Department", back_populates="faculty")
    sections = relationship("Section", back_populates="faculty")
    preferences = relationship("FacultyPreference", back_populates="faculty", cascade="all, delete-orphan")
    course_assignments = relationship("FacultyCourse", back_populates="faculty", cascade="all, delete-orphan")


class FacultyPreference(Base):
    """
    Faculty time preferences model.
    Stores faculty's preferred and unavailable time slots.
    
    Attributes:
        id: Primary key
        faculty_id: Foreign key to faculty table
        day_of_week: Day of week (0=Monday, 1=Tuesday, ..., 6=Sunday)
        time_slot_id: Foreign key to time_slots table
        preference_type: Type of preference ("preferred" or "not_available")
        created_at: Timestamp when preference was set
        updated_at: Timestamp when preference was last updated
        
    Relationships:
        faculty: Reference to Faculty model
        time_slot: Reference to TimeSlot model
        
    Test Coverage: tests/test_faculty.py::test_faculty_preference_creation
    """
    __tablename__ = "faculty_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)  # 0-6: Monday-Sunday
    time_slot_id = Column(Integer, ForeignKey("time_slots.id"), nullable=False)
    preference_type = Column(String(20), nullable=False)  # "preferred" or "not_available"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
    # Relationships
    faculty = relationship("Faculty", back_populates="preferences")
    time_slot = relationship("TimeSlot", back_populates="faculty_preferences")
