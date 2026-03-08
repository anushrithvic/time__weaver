"""
Unit Tests for Epic 3 Phase 2 Schema Updates

Tests all model updates and new models:
- Updated: Semester, Section, Room, Course, ElectiveGroup, TimetableSlot
- New: Curriculum, CourseElectiveAssignment, CourseBatchingConfig

Run with: pytest tests/test_models/test_epic3_phase2_models.py -v
"""

import pytest
from datetime import date, datetime
from sqlalchemy.exc import IntegrityError
from app.models.semester import Semester, SemesterType
from app.models.section import Section
from app.models.room import Room
from app.models.course import Course, ElectiveGroup, CourseCategory
from app.models.curriculum import Curriculum, CourseElectiveAssignment, CourseBatchingConfig
from app.models.timetable import TimetableSlot
from app.db.session import SessionLocal


@pytest.fixture
def db():
    """Database session fixture"""
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


class TestSemesterUpdates:
    """Test Semester model with semester_type enum"""
    
    def test_create_semester_with_odd_type(self, db):
        semester = Semester(
            name="Fall 2025",
            academic_year="2025-2026",
            semester_type=SemesterType.ODD,
            start_date=date(2025, 8, 15),
            end_date=date(2025, 12, 20),
            is_active=True
        )
        db.add(semester)
        db.commit()
        
        assert semester.id is not None
        assert semester.semester_type == SemesterType.ODD
        assert semester.name == "Fall 2025"
    
    def test_create_semester_with_even_type(self, db):
        semester = Semester(
            name="Spring 2026",
            academic_year="2025-2026",
            semester_type=SemesterType.EVEN,
            start_date=date(2026, 1, 10),
            end_date=date(2026, 5, 15),
            is_active=False
        )
        db.add(semester)
        db.commit()
        
        assert semester.semester_type == SemesterType.EVEN
    
    def test_semester_type_required(self, db):
        """Semester type is mandatory"""
        semester = Semester(
            name="Fall 2025",
            academic_year="2025-2026",
            start_date=date(2025, 8, 15),
            end_date=date(2025, 12, 20)
            # Missing semester_type
        )
        db.add(semester)
        
        with pytest.raises(IntegrityError):
            db.commit()


class TestSectionBatchUpdates:
    """Test Section model with batch lifecycle fields"""
    
    def test_create_section_with_batch_years(self, db):
        from app.models.department import Department
        
        dept = Department(name="Computer Science", code="CSE")
        db.add(dept)
        db.flush()
        
        section = Section(
            department_id=dept.id,
            name="CSE-A",
            batch_year_start=2023,
            batch_year_end=2027,
            student_count=60
        )
        db.add(section)
        db.commit()
        
        assert section.batch_year_start == 2023
        assert section.batch_year_end == 2027
        assert section.name == "CSE-A"
    
    def test_section_with_dedicated_room(self, db):
        from app.models.department import Department
        
        dept = Department(name="CSE", code="CSE")
        room = Room(
            building="ABIII",
            room_number="C302",
            full_name="ABIII - C302",
            room_type="classroom",
            capacity=60
        )
        db.add_all([dept, room])
        db.flush()
        
        section = Section(
            department_id=dept.id,
            name="CSE-A",
            batch_year_start=2023,
            batch_year_end=2027,
            student_count=60,
            dedicated_room_id=room.id
        )
        db.add(section)
        db.commit()
        
        assert section.dedicated_room_id == room.id
    
    def test_section_with_class_advisors(self, db):
        from app.models.department import Department
        
        dept = Department(name="CSE", code="CSE")
        db.add(dept)
        db.flush()
        
        section = Section(
            department_id=dept.id,
            name="CSE-G",
            batch_year_start=2024,
            batch_year_end=2028,
            student_count=65,
            class_advisor_ids=[101, 102]  # Array of User IDs
        )
        db.add(section)
        db.commit()
        
        assert section.class_advisor_ids == [101, 102]
    
    def test_batch_years_constraint(self, db):
        """batch_year_start must be less than batch_year_end"""
        from app.models.department import Department
        
        dept = Department(name="CSE", code="CSE")
        db.add(dept)
        db.flush()
        
        section = Section(
            department_id=dept.id,
            name="Invalid",
            batch_year_start=2027,  # Invalid: start > end
            batch_year_end=2023,
            student_count=60
        )
        db.add(section)
        
        with pytest.raises(IntegrityError):
            db.commit()


class TestRoomUpdates:
    """Test Room model with building/room_number/full_name split"""
    
    def test_create_room_with_split_fields(self, db):
        room = Room(
            building="ABIII",
            room_number="C302",
            full_name="ABIII - C302",
            room_type="classroom",
            capacity=60,
            floor=3
        )
        db.add(room)
        db.commit()
        
        assert room.building == "ABIII"
        assert room.room_number == "C302"
        assert room.full_name == "ABIII - C302"
    
    def test_full_name_unique_constraint(self, db):
        """full_name must be unique"""
        room1 = Room(
            building="ABIII",
            room_number="C302",
            full_name="ABIII - C302",
            room_type="classroom",
            capacity=60
        )
        room2 = Room(
            building="ABIII",
            room_number="C302",
            full_name="ABIII - C302",  # Duplicate
            room_type="lab",
            capacity=30
        )
        db.add_all([room1, room2])
        
        with pytest.raises(IntegrityError):
            db.commit()
    
    def test_building_required(self, db):
        """building field is now required"""
        room = Room(
            room_number="C302",
            full_name="C302",
            room_type="classroom",
            capacity=60
            # Missing building
        )
        db.add(room)
        
        with pytest.raises(IntegrityError):
            db.commit()


class TestCourseUpdates:
    """Test Course model with course_category enum"""
    
    def test_create_core_course(self, db):
        from app.models.department import Department
        
        dept = Department(name="CSE", code="CSE")
        db.add(dept)
        db.flush()
        
        course = Course(
            code="CS301",
            name="Data Structures",
            theory_hours=3,
            lab_hours=0,
            credits=3,
            department_id=dept.id,
            course_category=CourseCategory.CORE
        )
        db.add(course)
        db.commit()
        
        assert course.course_category == CourseCategory.CORE
    
    def test_create_professional_elective(self, db):
        from app.models.department import Department
        
        dept = Department(name="CSE", code="CSE")
        db.add(dept)
        db.flush()
        
        course = Course(
            code="CS501",
            name="Cryptography",
            theory_hours=3,
            lab_hours=0,
            credits=3,
            department_id=dept.id,
            course_category=CourseCategory.PROFESSIONAL_ELECTIVE
        )
        db.add(course)
        db.commit()
        
        assert course.course_category == CourseCategory.PROFESSIONAL_ELECTIVE
    
    def test_all_course_categories(self, db):
        """Test all course category types"""
        from app.models.department import Department
        
        dept = Department(name="CSE", code="CSE")
        db.add(dept)
        db.flush()
        
        categories = [
            CourseCategory.CORE,
            CourseCategory.PROFESSIONAL_ELECTIVE,
            CourseCategory.FREE_ELECTIVE,
            CourseCategory.PROJECT,
            CourseCategory.MENTORING
        ]
        
        for i, cat in enumerate(categories):
            course = Course(
                code=f"CS{i}01",
                name=f"Course {i}",
                theory_hours=1,
                lab_hours=0,
                credits=1,
                department_id=dept.id,
                course_category=cat
            )
            db.add(course)
        
        db.commit()
        assert db.query(Course).count() == 5


class TestElectiveGroupUpdates:
    """Test ElectiveGroup model - now permanent with participating depts"""
    
    def test_create_permanent_elective_group(self, db):
        """ElectiveGroup no longer requires semester_id"""
        group = ElectiveGroup(
            name="PE1",
            description="Professional Elective Group 1",
            participating_department_ids=[1, 2]  # CSE, ECE
        )
        db.add(group)
        db.commit()
        
        assert group.id is not None
        assert group.name == "PE1"
        assert group.participating_department_ids == [1, 2]
    
    def test_elective_group_name_unique(self, db):
        """Name must be unique"""
        group1 = ElectiveGroup(name="PE1", description="First")
        group2 = ElectiveGroup(name="PE1", description="Duplicate")
        
        db.add_all([group1, group2])
        
        with pytest.raises(IntegrityError):
            db.commit()
    
    def test_free_elective_multiple_departments(self, db):
        """Free electives can span multiple departments"""
        group = ElectiveGroup(
            name="FE1-EVS",
            description="Free Elective - Environmental Science",
            participating_department_ids=[1, 2, 3, 4]  # All depts
        )
        db.add(group)
        db.commit()
        
        assert len(group.participating_department_ids) == 4


class TestCurriculumModel:
    """Test NEW Curriculum model"""
    
    def test_create_curriculum_entry(self, db):
        from app.models.department import Department
        
        dept = Department(name="CSE", code="CSE")
        course = Course(
            code="CS301",
            name="Data Structures",
            theory_hours=3,
            credits=3,
            department_id=1,
            course_category=CourseCategory.CORE
        )
        db.add_all([dept, course])
        db.flush()
        
        curriculum = Curriculum(
            department_id=dept.id,
            year_level=3,
            semester_type=SemesterType.ODD,
            course_id=course.id,
            is_mandatory=True
        )
        db.add(curriculum)
        db.commit()
        
        assert curriculum.year_level == 3
        assert curriculum.semester_type == SemesterType.ODD
        assert curriculum.is_mandatory is True
    
    def test_year_level_constraint(self, db):
        """year_level must be 1-4"""
        curriculum = Curriculum(
            department_id=1,
            year_level=5,  # Invalid
            semester_type=SemesterType.ODD,
            course_id=1,
            is_mandatory=True
        )
        db.add(curriculum)
        
        with pytest.raises(IntegrityError):
            db.commit()
    
    def test_unique_curriculum_entry(self, db):
        """Can't have duplicate (dept, year, sem_type, course) entries"""
        curr1 = Curriculum(
            department_id=1,
            year_level=3,
            semester_type=SemesterType.ODD,
            course_id=101,
            is_mandatory=True
        )
        curr2 = Curriculum(
            department_id=1,
            year_level=3,
            semester_type=SemesterType.ODD,
            course_id=101,  # Duplicate
            is_mandatory=False
        )
        db.add_all([curr1, curr2])
        
        with pytest.raises(IntegrityError):
            db.commit()


class TestCourseElectiveAssignment:
    """Test NEW CourseElectiveAssignment model"""
    
    def test_create_elective_assignment(self, db):
        assignment = CourseElectiveAssignment(
            elective_group_id=1,
            semester_id=5,
            course_id=201,
            assigned_room_id=101
        )
        db.add(assignment)
        db.commit()
        
        assert assignment.elective_group_id == 1
        assert assignment.semester_id == 5
        assert assignment.assigned_room_id == 101
    
    def test_unique_assignment(self, db):
        """Can't assign same course to same group in same semester twice"""
        assign1 = CourseElectiveAssignment(
            elective_group_id=1,
            semester_id=5,
            course_id=201
        )
        assign2 = CourseElectiveAssignment(
            elective_group_id=1,
            semester_id=5,
            course_id=201  # Duplicate
        )
        db.add_all([assign1, assign2])
        
        with pytest.raises(IntegrityError):
            db.commit()


class TestCourseBatchingConfig:
    """Test NEW CourseBatchingConfig model"""
    
    def test_create_batching_config(self, db):
        config = CourseBatchingConfig(
            course_id=101,
            semester_id=5,
            num_batches=2,
            batch_size=30
        )
        db.add(config)
        db.commit()
        
        assert config.num_batches == 2
        assert config.batch_size == 30
    
    def test_num_batches_constraint(self, db):
        """num_batches must be 1-10"""
        config = CourseBatchingConfig(
            course_id=101,
            semester_id=5,
            num_batches=15,  # Invalid: > 10
            batch_size=10
        )
        db.add(config)
        
        with pytest.raises(IntegrityError):
            db.commit()
    
    def test_batch_size_positive(self, db):
        """batch_size must be > 0"""
        config = CourseBatchingConfig(
            course_id=101,
            semester_id=5,
            num_batches=2,
            batch_size=0  # Invalid
        )
        db.add(config)
        
        with pytest.raises(IntegrityError):
            db.commit()


class TestTimetableSlotUpdates:
    """Test TimetableSlot with multi-slot support"""
    
    def test_create_single_slot(self, db):
        """Regular 1-hour class"""
        slot = TimetableSlot(
            timetable_id=1,
            section_id=10,
            course_id=101,
            room_id=201,
            start_slot_id=4,
            duration_slots=1,
            day_of_week=0,
            primary_faculty_id=301,
            is_locked=False
        )
        db.add(slot)
        db.commit()
        
        assert slot.start_slot_id == 4
        assert slot.duration_slots == 1
        assert slot.primary_faculty_id == 301
    
    def test_create_multislot_cir(self, db):
        """3-hour CIR block"""
        slot = TimetableSlot(
            timetable_id=1,
            section_id=10,
            course_id=102,
            room_id=201,
            start_slot_id=4,
            duration_slots=3,  # Occupies slots 4, 5, 6
            day_of_week=1,
            primary_faculty_id=301,
            is_locked=True
        )
        db.add(slot)
        db.commit()
        
        assert slot.duration_slots == 3
        assert slot.is_locked is True
    
    def test_lab_with_batching(self, db):
        """Lab session with batch number"""
        slot = TimetableSlot(
            timetable_id=1,
            section_id=10,
            course_id=103,
            room_id=202,
            start_slot_id=5,
            duration_slots=2,
            day_of_week=2,
            primary_faculty_id=302,
            batch_number=1,  # Batch 1
            is_locked=False
        )
        db.add(slot)
        db.commit()
        
        assert slot.batch_number == 1
    
    def test_assisting_faculty(self, db):
        """Lab with multiple faculty"""
        slot = TimetableSlot(
            timetable_id=1,
            section_id=10,
            course_id=104,
            room_id=203,
            start_slot_id=6,
            duration_slots=2,
            day_of_week=3,
            primary_faculty_id=303,
            assisting_faculty_ids=[304, 305],  # 2 assistants
            is_locked=False
        )
        db.add(slot)
        db.commit()
        
        assert slot.primary_faculty_id == 303
        assert slot.assisting_faculty_ids == [304, 305]
    
    def test_duration_slots_constraint(self, db):
        """duration_slots must be 1-5"""
        slot = TimetableSlot(
            timetable_id=1,
            section_id=10,
            room_id=201,
            start_slot_id=4,
            duration_slots=10,  # Invalid: > 5
            day_of_week=0,
            is_locked=False
        )
        db.add(slot)
        
        with pytest.raises(IntegrityError):
            db.commit()
