# Import all models here for Alembic to detect them
from app.db.session import Base

# Import models (will be created next)
from app.models.semester import Semester, SemesterType
from app.models.department import Department
from app.models.section import Section
from app.models.course import Course, ElectiveGroup, CourseCategory
from app.models.room import Room
from app.models.time_slot import TimeSlot
from app.models.constraint import Constraint
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.timetable import Timetable, TimetableSlot, Conflict
from app.models.institutional_rule import InstitutionalRule, RuleType
from app.models.faculty_leave import FacultyLeave, LeaveType, LeaveStrategy, LeaveStatus
from app.models.curriculum import Curriculum, CourseElectiveAssignment, CourseBatchingConfig
from app.models.faculty import Faculty, FacultyPreference
