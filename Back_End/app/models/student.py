"""
Module: Student Management
Repository: timeweaver_backend

This module defines the Student database model.
Handles student profiles linked to users, departments, and sections.

Dependencies:
    - app.db.session (Base model)
    - app.models.user (User model)
    - app.models.department (Department model)
    - app.models.section (Section model)
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.session import Base


class Student(Base):
    """
    Student model representing a student member.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to users table (one-to-one)
        roll_no: Unique student roll number (e.g., "21CSE101")
        department_id: Foreign key to departments table
        section_id: Foreign key to sections table
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
        
    Relationships:
        user: Reference to User model
        department: Reference to Department model
        section: Reference to Section model
    """
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    roll_no = Column(String(20), unique=True, nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
    # Relationships
    user = relationship("User", back_populates="student")
    department = relationship("Department")
    section = relationship("Section")
