"""
Module: Timetable Generation & Scheduling (Module 3)
Repository: timeweaver_backend
Owner: Pranathi Nibhanipudi
Epic: 3 - Timetable Generation / Re-generation

Curriculum Service - Section Semester Calculation

Calculates which semester (1-8) a section is currently in and fetches
the appropriate courses for timetable generation based on batch lifecycle
and ODD/EVEN semester types.

Key Logic:
- Section has batch_year_start (e.g., 2023) and batch_year_end (2027)
- Semester has semester_type (ODD/EVEN) and year (e.g., 2025)
- Calculate: year_level = (current_year - batch_year_start) + 1
- Semester number = (year_level - 1) * 2 + (1 if ODD else 2)

Dependencies:
    - app.models.section (Section model)
    - app.models.semester (Semester, SemesterType)
    - app.models.curriculum (Curriculum model)
    - app.models.course (Course, CourseCategory)

User Stories: 3.3.2 (Multi-Solution Generation)
"""

from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.section import Section
from app.models.semester import Semester, SemesterType
from app.models.curriculum import Curriculum
from app.models.course import Course, CourseCategory


class CurriculumService:
    """Service for curriculum-related operations"""
    
    @staticmethod
    def get_section_year_level(section: Section, semester: Semester) -> int:
        """
        Calculate which year level (1-4) a section is in during a semester.
        
        Args:
            section: Section with batch_year_start/end
            semester: Semester being scheduled
            
        Returns:
            Year level (1-4)
            
        Example:
            Section: 2023-2027 batch
            Semester: Fall 2025
            Result: year_level = (2025 - 2023) + 1 = 3
        """
        # Extract year from semester (assuming academic_year format "2025-2026")
        semester_year = int(semester.academic_year.split('-')[0])
        
        year_level = (semester_year - section.batch_year_start) + 1
        
        # Clamp to 1-4
        return max(1, min(4, year_level))
    
    @staticmethod
    def get_section_semester_number(section: Section, semester: Semester) -> int:
        """
        Calculate which semester number (1-8) a section is in.
        
        Args:
            section: Section with batch lifecycle
            semester: Semester with type (ODD/EVEN)
            
        Returns:
            Semester number (1-8)
            
        Example:
            Year 3, ODD semester → Semester 5
            Year 3, EVEN semester → Semester 6
        """
        year_level = CurriculumService.get_section_year_level(section, semester)
        
        # Calculate semester number
        if semester.semester_type == SemesterType.ODD:
            semester_number = (year_level - 1) * 2 + 1
        else:  # EVEN
            semester_number = (year_level - 1) * 2 + 2
        
        return semester_number
    
    @staticmethod
    def get_core_courses_for_section(
        db: Session,
        section: Section,
        semester: Semester
    ) -> list[Course]:
        """
        Fetch all CORE (mandatory) courses for a section in a semester.
        
        Args:
            db: Database session
            section: Section to get courses for
            semester: Current semester
            
        Returns:
            List of core Course objects
        """
        year_level = CurriculumService.get_section_year_level(section, semester)
        
        # Query curriculum for core courses
        stmt = (
            select(Course)
            .join(Curriculum, Curriculum.course_id == Course.id)
            .where(
                Curriculum.department_id == section.department_id,
                Curriculum.year_level == year_level,
                Curriculum.semester_type == semester.semester_type,
                Curriculum.is_mandatory == True
            )
        )
        
        result = db.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    def get_elective_courses_for_section(
        db: Session,
        section: Section,
        semester: Semester
    ) -> dict[str, list[Course]]:
        """
        Fetch all elective courses (PE, FE) for a section in a semester.
        
        Args:
            db: Database session
            section: Section to get electives for
            semester: Current semester
            
        Returns:
            Dict with elective group names as keys, course lists as values
            Example: {"PE1": [Course1, Course2], "FE1": [Course3]}
        """
        year_level = CurriculumService.get_section_year_level(section, semester)
        
        # Query curriculum for elective courses
        stmt = (
            select(Course)
            .join(Curriculum, Curriculum.course_id == Course.id)
            .where(
                Curriculum.department_id == section.department_id,
                Curriculum.year_level == year_level,
                Curriculum.semester_type == semester.semester_type,
                Curriculum.is_mandatory == False,
                Course.course_category.in_([
                    CourseCategory.PROFESSIONAL_ELECTIVE,
                    CourseCategory.FREE_ELECTIVE
                ])
            )
        )
        
        result = db.execute(stmt)
        electives = list(result.scalars().all())
        
        # Group by elective_group_id (would need to join ElectiveGroup for names)
        # For now, return as simple list
        return {"electives": electives}
    
    @staticmethod
    def get_all_courses_for_section(
        db: Session,
        section: Section,
        semester: Semester
    ) -> dict[str, any]:
        """
        Fetch ALL courses (core + electives + projects + mentoring) for a section.
        
        Args:
            db: Database session
            section: Section to get courses for
            semester: Current semester
            
        Returns:
            Dict with categorized courses
        """
        year_level = CurriculumService.get_section_year_level(section, semester)
        
        # Get all courses from curriculum
        stmt = (
            select(Course, Curriculum.is_mandatory)
            .join(Curriculum, Curriculum.course_id == Course.id)
            .where(
                Curriculum.department_id == section.department_id,
                Curriculum.year_level == year_level,
                Curriculum.semester_type == semester.semester_type
            )
        )
        
        result = db.execute(stmt)
        rows = result.all()
        
        # Categorize courses
        core_courses = []
        elective_courses = []
        project_courses = []
        mentoring_courses = []
        
        for course, is_mandatory in rows:
            if course.course_category == CourseCategory.CORE:
                core_courses.append(course)
            elif course.course_category in [
                CourseCategory.PROFESSIONAL_ELECTIVE,
                CourseCategory.FREE_ELECTIVE
            ]:
                elective_courses.append(course)
            elif course.course_category == CourseCategory.PROJECT:
                project_courses.append(course)
            elif course.course_category == CourseCategory.MENTORING:
                mentoring_courses.append(course)
        
        return {
            "core": core_courses,
            "electives": elective_courses,
            "projects": project_courses,
            "mentoring": mentoring_courses,
            "total_count": len(rows)
        }
