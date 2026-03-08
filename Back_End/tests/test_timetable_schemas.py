"""
Module: Testing Timetable Schemas (Module 3)
Repository: timeweaver_backend
Owner: Pranathi Nibhanipudi

Unit tests for Pydantic schemas used in timetable API endpoints.
Tests validation, serialization, and error handling.

Run with: pytest tests/test_timetable_schemas.py -v
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.timetable import (
    TimetableCreate,
    TimetableResponse,
    TimetableSlotResponse,
    ConflictResponse,
    SlotLockRequest,
    FacultyLeaveRequest,
    AddSectionRequest,
    GenerationStatusResponse,
    GenerationAlgorithm,
    TimetableStatus,
    ConflictType,
    ConflictSeverity
)


class TestTimetableCreateSchema:
    """Test cases for TimetableCreate request schema"""
    
    def test_create_with_defaults(self):
        """Test creation with default values"""
        data = {"semester_id": 1}
        schema = TimetableCreate(**data)
        
        assert schema.semester_id == 1
        assert schema.algorithm == GenerationAlgorithm.GA
        assert schema.num_solutions == 5
        assert schema.max_generations == 100
        assert schema.population_size == 50
    
    def test_create_with_custom_values(self):
        """Test creation with custom parameters"""
        data = {
            "semester_id": 1,
            "algorithm": "SA",
            "num_solutions": 3,
            "max_generations": 200,
            "population_size": 100
        }
        schema = TimetableCreate(**data)
        
        assert schema.algorithm == GenerationAlgorithm.SA
        assert schema.num_solutions == 3
        assert schema.max_generations == 200
        assert schema.population_size == 100
    
    def test_invalid_semester_id(self):
        """Test that semester_id must be positive"""
        with pytest.raises(ValidationError) as exc_info:
            TimetableCreate(semester_id=0)
        
        assert "semester_id" in str(exc_info.value)
    
    def test_num_solutions_range_validation(self):
        """Test that num_solutions must be 1-10"""
        # Test too low
        with pytest.raises(ValidationError):
            TimetableCreate(semester_id=1, num_solutions=0)
        
        # Test too high
        with pytest.raises(ValidationError):
            TimetableCreate(semester_id=1, num_solutions=11)
    
    def test_max_generations_range(self):
        """Test max_generations constraints"""
        # Test too low
        with pytest.raises(ValidationError):
            TimetableCreate(semester_id=1, max_generations=5)
        
        # Test too high
        with pytest.raises(ValidationError):
            TimetableCreate(semester_id=1, max_generations=1000)
    
    def test_population_size_range(self):
        """Test population_size constraints"""
        # Test too low
        with pytest.raises(ValidationError):
            TimetableCreate(semester_id=1, population_size=5)
        
        # Test too high
        with pytest.raises(ValidationError):
            TimetableCreate(semester_id=1, population_size=300)


class TestSlotLockRequest:
    """Test cases for SlotLockRequest schema"""
    
    def test_valid_slot_lock_request(self):
        """Test valid slot lock request"""
        data = {"slot_ids": [1, 2, 3, 4]}
        schema = SlotLockRequest(**data)
        
        assert schema.slot_ids == [1, 2, 3, 4]
        assert len(schema.slot_ids) == 4
    
    def test_empty_slot_ids_invalid(self):
        """Test that empty slot_ids list is invalid"""
        with pytest.raises(ValidationError) as exc_info:
            SlotLockRequest(slot_ids=[])
        
        assert "slot_ids" in str(exc_info.value)


class TestFacultyLeaveRequest:
    """Test cases for FacultyLeaveRequest schema"""
    
    def test_valid_leave_request(self):
        """Test valid faculty leave request"""
        data = {
            "faculty_id": 10,
            "start_date": datetime(2024, 10, 1),
            "end_date": datetime(2024, 10, 7)
        }
        schema = FacultyLeaveRequest(**data)
        
        assert schema.faculty_id == 10
        assert schema.start_date.year == 2024
        assert schema.end_date.year == 2024
    
    def test_end_before_start_invalid(self):
        """Test that end_date must be after start_date"""
        data = {
            "faculty_id": 10,
            "start_date": datetime(2024, 10, 7),
            "end_date": datetime(2024, 10, 1)  # Before start!
        }
        
        with pytest.raises(ValidationError) as exc_info:
            FacultyLeaveRequest(**data)
        
        assert "end_date must be after start_date" in str(exc_info.value)
    
    def test_invalid_faculty_id(self):
        """Test that faculty_id must be positive"""
        with pytest.raises(ValidationError):
            FacultyLeaveRequest(
                faculty_id=0,
                start_date=datetime(2024, 10, 1),
                end_date=datetime(2024, 10, 7)
            )


class TestAddSectionRequest:
    """Test cases for AddSectionRequest schema"""
    
    def test_valid_add_section(self):
        """Test valid add section request"""
        schema = AddSectionRequest(section_id=42)
        assert schema.section_id == 42
    
    def test_invalid_section_id(self):
        """Test that section_id must be positive"""
        with pytest.raises(ValidationError):
            AddSectionRequest(section_id=0)


class TestTimetableResponse:
    """Test cases for TimetableResponse schema"""
    
    def test_from_orm_model(self):
        """Test creating response from ORM model"""
        # Mock ORM model
        class MockTimetable:
            id = 1
            semester_id = 1
            name = "Fall 2024 - GA v1"
            status = "completed"
            quality_score = 0.92
            conflict_count = 0
            is_published = False
            generation_algorithm = "GA"
            generation_time_seconds = 25.5
            created_by_user_id = 1
            created_at = datetime(2024, 9, 1)
            updated_at = datetime(2024, 9, 1)
            published_at = None
        
        schema = TimetableResponse.model_validate(MockTimetable())
        
        assert schema.id == 1
        assert schema.name == "Fall 2024 - GA v1"
        assert schema.status == TimetableStatus.COMPLETED
        assert schema.quality_score == 0.92
        assert schema.generation_algorithm == GenerationAlgorithm.GA


class TestConflictResponse:
    """Test cases for ConflictResponse schema"""
    
    def test_conflict_response_creation(self):
        """Test conflict response creation"""
        # Mock ORM model
        class MockConflict:
            id = 1
            timetable_id = 1
            conflict_type = "ROOM_CLASH"
            severity = "HIGH"
            slot_ids = [101, 102]
            description = "Room 201: CSE-A and ECE-B at Monday 9:00"
            is_resolved = False
            resolution_notes = None
            detected_at = datetime(2024, 9, 1, 10, 0)
            resolved_at = None
        
        schema = ConflictResponse.model_validate(MockConflict())
        
        assert schema.id == 1
        assert schema.conflict_type == ConflictType.ROOM_CLASH
        assert schema.severity == ConflictSeverity.HIGH
        assert schema.slot_ids == [101, 102]
        assert schema.is_resolved is False


class TestGenerationStatusResponse:
    """Test cases for GenerationStatusResponse schema"""
    
    def test_pending_status(self):
        """Test pending generation status"""
        data = {
            "job_id": "abc-123",
            "status": "PENDING",
            "message": "Waiting for worker"
        }
        schema = GenerationStatusResponse(**data)
        
        assert schema.job_id == "abc-123"
        assert schema.status == "PENDING"
        assert schema.progress_percent is None
    
    def test_progress_status(self):
        """Test in-progress generation status"""
        data = {
            "job_id": "abc-123",
            "status": "PROGRESS",
            "progress_percent": 45,
            "current_generation": 45,
            "total_generations": 100,
            "message": "Evolving population"
        }
        schema = GenerationStatusResponse(**data)
        
        assert schema.status == "PROGRESS"
        assert schema.progress_percent == 45
        assert schema.current_generation == 45
    
    def test_success_status(self):
        """Test successful generation status"""
        data = {
            "job_id": "abc-123",
            "status": "SUCCESS",
            "progress_percent": 100,
            "result": 42,  # Timetable ID
            "message": "Generation complete"
        }
        schema = GenerationStatusResponse(**data)
        
        assert schema.status == "SUCCESS"
        assert schema.result == 42
    
    def test_progress_percent_range(self):
        """Test that progress_percent is 0-100"""
        # Test too high
        with pytest.raises(ValidationError):
            GenerationStatusResponse(
                job_id="test",
                status="PROGRESS",
                progress_percent=150
            )
        
        # Test negative
        with pytest.raises(ValidationError):
            GenerationStatusResponse(
                job_id="test",
                status="PROGRESS",
                progress_percent=-10
            )


class TestEnums:
    """Test cases for enum types"""
    
    def test_generation_algorithm_enum(self):
        """Test GenerationAlgorithm enum values"""
        assert GenerationAlgorithm.GA == "GA"
        assert GenerationAlgorithm.SA == "SA"
        assert GenerationAlgorithm.HYBRID == "HYBRID"
        assert GenerationAlgorithm.CSP_GREEDY == "CSP_GREEDY"
    
    def test_timetable_status_enum(self):
        """Test TimetableStatus enum values"""
        assert TimetableStatus.GENERATING == "generating"
        assert TimetableStatus.COMPLETED == "completed"
        assert TimetableStatus.FAILED == "failed"
        assert TimetableStatus.ARCHIVED == "archived"
    
    def test_conflict_type_enum(self):
        """Test ConflictType enum values"""
        assert ConflictType.ROOM_CLASH == "ROOM_CLASH"
        assert ConflictType.FACULTY_CLASH == "FACULTY_CLASH"
        assert ConflictType.STUDENT_CLASH == "STUDENT_CLASH"
        assert ConflictType.CAPACITY_VIOLATION == "CAPACITY_VIOLATION"
    
    def test_conflict_severity_enum(self):
        """Test ConflictSeverity enum values"""
        assert ConflictSeverity.HIGH == "HIGH"
        assert ConflictSeverity.MEDIUM == "MEDIUM"
        assert ConflictSeverity.LOW == "LOW"
