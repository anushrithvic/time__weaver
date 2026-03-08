from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, CheckConstraint, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Section(Base):
    """
    Section model - represents a class section
    Section model - represents a permanent batch-based section with home room and advisor fields.

    Attributes:
        id (int): Primary key
        department_id (int): Foreign key to departments table
        name (str): Section name (e.g., "CSE-A", "CSE-G")
        batch_year_start (int): Starting year of the batch (e.g., 2023 for 2023-2027 batch)
        batch_year_end (int): Ending year of the batch (e.g., 2027 for 2023-2027 batch)
        student_count (int): Number of students enrolled
        dedicated_room_id (int): Foreign key to rooms table (home room for soft constraint)
        class_advisor_ids (list[int]): Array of User IDs who are class advisors (for mentoring)
        created_at (datetime): Timestamp when record was created
    """
    __tablename__ = "sections"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Core Fields
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=True)  # Primary faculty for this section
    name = Column(String(50), nullable=False)  # Section name (e.g., "CSE-A")
    
    # Batch lifecycle (permanent over 4 years)
    batch_year_start = Column(Integer, nullable=False)  # E.g., 2023
    batch_year_end = Column(Integer, nullable=False)  # E.g., 2027
    
    student_count = Column(Integer, nullable=False)  # Number of students
    
    # Home room (soft constraint - weight 0.9)
    dedicated_room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True, index=True)
    
    # Class advisors (for mentoring sessions)
    class_advisor_ids = Column(ARRAY(Integer), default=list)  # Array of User IDs
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    faculty = relationship("Faculty", back_populates="sections")
    # department = relationship("Department", back_populates="sections")
    # dedicated_room = relationship("Room", back_populates="sections") # Assuming Room model exists
    
    def __repr__(self):
        return f"<Section(id={self.id}, name='{self.name}', batch_year_start={self.batch_year_start}, batch_year_end={self.batch_year_end})>"
