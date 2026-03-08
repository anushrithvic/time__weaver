"""
User Management API Endpoints

Epic 7: User Story 7.1 - Role-Based Access Control (RBAC)

This module provides comprehensive user management functionality including:
- User CRUD operations (admin only)
- Self-service profile management
- Password management
- User listing with pagination and filtering
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from typing import Optional

from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.faculty import Faculty
from app.models.student import Student
from app.models.department import Department
from app.models.section import Section
from app.models.audit_log import AuditLog
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserUpdatePassword,
    UserResponse,
    UserListResponse,
    CreateFacultyUser,
    FacultyUserResponse,
    CreateStudentUser,
    StudentUserResponse
)
from app.core.security import hash_password, verify_password
from app.core.dependencies import get_current_user, get_current_admin

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Create a new user (Admin only)
    
    **Epic 7: User Story 7.1** - Role-based access control
    
    **Permissions:** Admin only
    
    **Request Body:**
    - username: Unique username
    - email: Unique email address
    - password: Password (will be hashed)
    - full_name: User's full name
    - role: User role (admin, faculty, student)
    - is_active: Whether user is active (default: true)
    - faculty_id: Optional link to faculty entity
    - student_id: Optional link to student entity
    """
    # Check if username already exists
    query = select(User).where(User.username == user_in.username)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_in.username}' already exists"
        )
    
    # Check if email already exists
    email_query = select(User).where(User.email == user_in.email)
    email_result = await db.execute(email_query)
    existing_email = email_result.scalar_one_or_none()
    
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{user_in.email}' already exists"
        )
    
    # Create user with hashed password
    user_data = user_in.model_dump(exclude={'password'})
    user_data['hashed_password'] = hash_password(user_in.password)
    
    user = User(**user_data)
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_admin.id,
        action="create",
        entity_type="user",
        entity_id=user.id,
        changes={
            "after": {
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "is_active": user.is_active
            }
        }
    )
    db.add(audit_log)
    await db.commit()
    
    return user


@router.post("/create-faculty", response_model=FacultyUserResponse, status_code=status.HTTP_201_CREATED)
async def create_faculty_user(
    data: CreateFacultyUser,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Create a new faculty member (User + Faculty profile) in one step. (Admin only)
    
    This is the **preferred endpoint** for registering faculty. It creates both the
    User account (with role=faculty) and the Faculty profile in a single transaction.
    
    **Permissions:** Admin only
    
    **Request Body:**
    - username: Unique username for login
    - email: Unique email address
    - password: Password (must meet strength requirements)
    - full_name: Faculty member's full name
    - employee_id: Unique employee identifier (e.g., "FAC001")
    - department_id: ID of the department the faculty belongs to
    - designation: Faculty designation (default: "Lecturer")
    - max_hours_per_week: Maximum teaching hours per week (default: 18)
    
    **Example:**
    ```json
    {
        "username": "dr_sharma",
        "email": "sharma@university.edu",
        "password": "SecureP@ss123",
        "full_name": "Dr. Priya Sharma",
        "employee_id": "FAC001",
        "department_id": 1,
        "designation": "Professor",
        "max_hours_per_week": 20
    }
    ```
    """
    # Check username uniqueness
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{data.username}' already exists"
        )
    
    # Check email uniqueness
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{data.email}' already exists"
        )
    
    # Check employee_id uniqueness
    result = await db.execute(select(Faculty).where(Faculty.employee_id == data.employee_id))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employee ID '{data.employee_id}' already exists"
        )
    
    # Verify department exists
    result = await db.execute(select(Department).where(Department.id == data.department_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with id {data.department_id} not found"
        )
    
    # Create User with role=faculty
    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=UserRole.FACULTY.value,
        is_active=True
    )
    db.add(user)
    await db.flush()  # Get user.id without committing
    
    # Create Faculty profile linked to the user
    faculty = Faculty(
        user_id=user.id,
        employee_id=data.employee_id,
        department_id=data.department_id,
        designation=data.designation,
        max_hours_per_week=data.max_hours_per_week
    )
    db.add(faculty)
    await db.flush()  # Get faculty.id
    
    # Link user back to faculty
    user.faculty_id = faculty.id
    
    # Audit log
    audit_log = AuditLog(
        user_id=current_admin.id,
        action="create",
        entity_type="faculty_user",
        entity_id=user.id,
        changes={
            "after": {
                "username": user.username,
                "email": user.email,
                "role": "faculty",
                "employee_id": data.employee_id,
                "department_id": data.department_id,
                "designation": data.designation
            }
        }
    )
    db.add(audit_log)
    
    # Commit everything in one transaction
    await db.commit()
    await db.refresh(user)
    await db.refresh(faculty)
    
    return FacultyUserResponse(
        user=UserResponse.model_validate(user),
        faculty_id=faculty.id,
        employee_id=faculty.employee_id,
        department_id=faculty.department_id,
        designation=faculty.designation,
        max_hours_per_week=faculty.max_hours_per_week
    )


@router.post("/create-student", response_model=StudentUserResponse, status_code=status.HTTP_201_CREATED)
async def create_student_user(
    data: CreateStudentUser,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Create a new student (User + Student profile) in one step. (Admin only)
    
    Creates both the User account (with role=student) and the Student profile
    in a single transaction.
    
    **Permissions:** Admin only
    
    **Request Body:**
    - username: Unique username for login
    - email: Unique email address
    - password: Password (must meet strength requirements)
    - full_name: Student's full name
    - roll_no: Unique roll number (e.g., "21CSE101")
    - department_id: ID of the department
    - section_id: ID of the section (must belong to the department)
    
    **Example:**
    ```json
    {
        "username": "student_ravi",
        "email": "ravi@university.edu",
        "password": "SecureP@ss123",
        "full_name": "Ravi Kumar",
        "roll_no": "21CSE101",
        "department_id": 1,
        "section_id": 3
    }
    ```
    """
    # Check username uniqueness
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{data.username}' already exists"
        )
    
    # Check email uniqueness
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{data.email}' already exists"
        )
    
    # Check roll_no uniqueness
    result = await db.execute(select(Student).where(Student.roll_no == data.roll_no))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Roll number '{data.roll_no}' already exists"
        )
    
    # Verify department exists
    result = await db.execute(select(Department).where(Department.id == data.department_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with id {data.department_id} not found"
        )
    
    # Verify section exists and belongs to the department
    result = await db.execute(
        select(Section).where(
            Section.id == data.section_id,
            Section.department_id == data.department_id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section with id {data.section_id} not found in department {data.department_id}"
        )
    
    # Create User with role=student
    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=UserRole.STUDENT.value,
        is_active=True
    )
    db.add(user)
    await db.flush()
    
    # Create Student profile linked to the user
    student = Student(
        user_id=user.id,
        roll_no=data.roll_no,
        department_id=data.department_id,
        section_id=data.section_id
    )
    db.add(student)
    await db.flush()
    
    # Link user back to student
    user.student_id = student.id
    
    # Audit log
    audit_log = AuditLog(
        user_id=current_admin.id,
        action="create",
        entity_type="student_user",
        entity_id=user.id,
        changes={
            "after": {
                "username": user.username,
                "email": user.email,
                "role": "student",
                "roll_no": data.roll_no,
                "department_id": data.department_id,
                "section_id": data.section_id
            }
        }
    )
    db.add(audit_log)
    
    # Commit everything in one transaction
    await db.commit()
    await db.refresh(user)
    await db.refresh(student)
    
    return StudentUserResponse(
        user=UserResponse.model_validate(user),
        student_id=student.id,
        roll_no=student.roll_no,
        department_id=student.department_id,
        section_id=student.section_id
    )


@router.get("/", response_model=UserListResponse)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    List all users with pagination and filtering (Admin only)
    
    **Permissions:** Admin only
    
    **Query Parameters:**
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    - role: Filter by user role (admin, faculty, student)
    - is_active: Filter by active status
    """
    # Build query
    query = select(User)
    
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
    
    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()
    
    # Get total count
    count_query = select(func.count()).select_from(User)
    if role:
        count_query = count_query.where(User.role == role)
    if is_active is not None:
        count_query = count_query.where(User.is_active == is_active)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    return UserListResponse(
        data=users,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Get a specific user by ID (Admin only)
    
    **Permissions:** Admin only
    """
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Update a user (Admin only)
    
    **Permissions:** Admin only
    
    **Note:** Cannot update password through this endpoint.
    Use PUT /users/{user_id}/password instead.
    """
    # Get existing user
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    # Store before values for audit
    before_values = {
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "is_active": user.is_active
    }
    
    # Update fields
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    # Store after values
    after_values = {
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "is_active": user.is_active
    }
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_admin.id,
        action="update",
        entity_type="user",
        entity_id=user.id,
        changes={
            "before": before_values,
            "after": after_values
        }
    )
    db.add(audit_log)
    await db.commit()
    
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Deactivate a user (Admin only)
    
    **Permissions:** Admin only
    
    **Note:** This performs a soft delete by setting is_active to False.
    The user record is not physically deleted from the database.
    """
    # Prevent admin from deleting themselves
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    # Soft delete: set is_active to False
    user.is_active = False
    
    await db.commit()
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_admin.id,
        action="delete",
        entity_type="user",
        entity_id=user.id,
        changes={
            "before": {"is_active": True},
            "after": {"is_active": False}
        }
    )
    db.add(audit_log)
    await db.commit()
    
    return None


@router.get("/me/profile", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's profile
    
    **Permissions:** Any authenticated user
    
    Returns the profile information of the currently logged-in user.
    """
    return current_user


@router.put("/me/profile", response_model=UserResponse)
async def update_my_profile(
    profile_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update current user's own profile
    
    **Permissions:** Any authenticated user
    
    **Note:** Users cannot change their own role or active status.
    Only email and full_name can be updated.
    """
    # Prevent role and active status change
    if profile_update.role is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own role"
        )
    
    if profile_update.is_active is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own active status"
        )
    
    # Store before values
    before_values = {
        "email": current_user.email,
        "full_name": current_user.full_name
    }
    
    # Update allowed fields only
    update_data = profile_update.model_dump(
        exclude_unset=True,
        exclude={'role', 'is_active'}
    )
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    
    # Store after values
    after_values = {
        "email": current_user.email,
        "full_name": current_user.full_name
    }
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action="update",
        entity_type="user",
        entity_id=current_user.id,
        changes={
            "before": before_values,
            "after": after_values
        }
    )
    db.add(audit_log)
    await db.commit()
    
    return current_user


@router.put("/me/password", status_code=status.HTTP_200_OK)
async def change_my_password(
    password_update: UserUpdatePassword,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Change current user's password
    
    **Permissions:** Any authenticated user
    
    **Request Body:**
    - current_password: Current password for verification
    - new_password: New password (must meet strength requirements)
    
    **Password Requirements:**
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    """
    # Verify current password
    if not verify_password(password_update.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.hashed_password = hash_password(password_update.new_password)
    
    await db.commit()
    
    # Create audit log (don't log password values)
    audit_log = AuditLog(
        user_id=current_user.id,
        action="update",
        entity_type="user",
        entity_id=current_user.id,
        changes={
            "action_description": "Password changed"
        }
    )
    db.add(audit_log)
    await db.commit()
    
    return {"message": "Password updated successfully"}
