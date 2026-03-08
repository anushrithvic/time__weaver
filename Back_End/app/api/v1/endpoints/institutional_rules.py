"""
Module: Institutional Rules API Endpoints (Module 3)
Repository: timeweaver_backend
Owner: Pranathi Nibh

anipudi
Epic: 3 - Timetable Generation / Re-generation

REST API endpoints for managing institutional rules.

Key Endpoints:
    POST   /api/v1/rules - Create new rule
    GET    /api/v1/rules - List all rules with filters
    GET    /api/v1/rules/{id} - Get specific rule
    PUT    /api/v1/rules/{id} - Update rule
    DELETE /api/v1/rules/{id} - Delete rule
    PATCH  /api/v1/rules/{id}/toggle - Enable/disable rule

Dependencies:
    - app.models.institutional_rule (InstitutionalRule, RuleType)
    - app.services.rule_engine (RuleEngine)

User Stories: 3.5.2 (Institutional Rules)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.core.dependencies import get_current_admin, get_current_user
from app.models.institutional_rule import InstitutionalRule, RuleType
from pydantic import BaseModel, Field

router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class RuleCreate(BaseModel):
    """Request schema for creating institutional rule"""
    name: str = Field(..., min_length=1, max_length=200, description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    rule_type: RuleType = Field(..., description="Rule type")
    configuration: dict = Field(..., description="JSON configuration")
    is_hard_constraint: bool = Field(True, description="Hard vs soft constraint")
    weight: float = Field(1.0, ge=0.0, le=1.0, description="Weight for soft constraints")
    applies_to_departments: list[int] = Field(default=[], description="Department IDs (empty = all)")
    applies_to_years: list[int] = Field(default=[], description="Year levels 1-4 (empty = all)")
    is_active: bool = Field(True, description="Whether rule is enabled")


class RuleUpdate(BaseModel):
    """Request schema for updating institutional rule"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    configuration: Optional[dict] = None
    is_hard_constraint: Optional[bool] = None
    weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    applies_to_departments: Optional[list[int]] = None
    applies_to_years: Optional[list[int]] = None
    is_active: Optional[bool] = None


class RuleResponse(BaseModel):
    """Response schema for institutional rule"""
    id: int
    name: str
    description: Optional[str]
    rule_type: str
    configuration: dict
    is_hard_constraint: bool
    weight: float
    applies_to_departments: list[int]
    applies_to_years: list[int]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class RuleListResponse(BaseModel):
    """Response schema for list of rules"""
    data: list[RuleResponse]
    total: int


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_error_response(error: str, message: str, code: int):
    """Create structured error response"""
    return {
        "error": error,
        "message": message,
        "code": code
    }


# ============================================================================
# RULE CRUD ENDPOINTS
# ============================================================================

@router.post("/", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    rule_in: RuleCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Create a new institutional rule.
    
    **Epic 3: User Story 3.5.2** - Institutional Rules
    **Permissions:** Admin only
    
    Args:
        rule_in: Rule data
        db: Database session
        current_admin: Current admin user
        
    Returns:
        RuleResponse: Created rule
        
    Raises:
        400: Rule name already exists
        
    Example:
        ```
        POST /api/v1/rules
        {
            "name": "No Early Morning Classes",
            "description": "No classes before 9 AM",
            "rule_type": "TIME_WINDOW",
            "configuration": {"min_slot": 2, "max_slot": 8},
            "is_hard_constraint": true,
            "weight": 1.0
        }
        ```
    """
    # Check if name already exists
    query = select(InstitutionalRule).where(InstitutionalRule.name == rule_in.name)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                "DUPLICATE_NAME",
                f"Rule with name '{rule_in.name}' already exists",
                400
            )
        )
    
    # Validate configuration based on rule type
    try:
        _validate_rule_configuration(rule_in.rule_type, rule_in.configuration)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                "INVALID_CONFIGURATION",
                str(e),
                400
            )
        )
    
    rule = InstitutionalRule(**rule_in.model_dump())
    
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    
    return rule


@router.get("/", response_model=RuleListResponse)
async def list_rules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    rule_type: Optional[RuleType] = Query(None, description="Filter by rule type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_hard_constraint: Optional[bool] = Query(None, description="Filter by constraint type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all institutional rules with optional filters.
    
    **Permissions:** All authenticated users
    
    Args:
        skip: Pagination offset
        limit: Max results
        rule_type: Filter by rule type
        is_active: Filter by active status
        is_hard_constraint: Filter by constraint type
        db: Database session
        current_user: Current user
        
    Returns:
        RuleListResponse: List of rules with total count
        
    Example:
        ```
        GET /api/v1/rules?rule_type=TIME_WINDOW&is_active=true
        ```
    """
    query = select(InstitutionalRule)
    
    # Apply filters
    if rule_type:
        query = query.where(InstitutionalRule.rule_type == rule_type)
    if is_active is not None:
        query = query.where(InstitutionalRule.is_active == is_active)
    if is_hard_constraint is not None:
        query = query.where(InstitutionalRule.is_hard_constraint == is_hard_constraint)
    
    # Order by name
    query = query.order_by(InstitutionalRule.name)
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    rules = result.scalars().all()
    
    # Get total count
    count_query = select(func.count()).select_from(InstitutionalRule)
    if rule_type:
        count_query = count_query.where(InstitutionalRule.rule_type == rule_type)
    if is_active is not None:
        count_query = count_query.where(InstitutionalRule.is_active == is_active)
    if is_hard_constraint is not None:
        count_query = count_query.where(InstitutionalRule.is_hard_constraint == is_hard_constraint)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    return RuleListResponse(data=rules, total=total)


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific institutional rule by ID.
    
    **Permissions:** All authenticated users
    
    Args:
        rule_id: Rule ID
        db: Database session
        current_user: Current user
        
    Returns:
        RuleResponse: Rule details
        
    Raises:
        404: Rule not found
        
    Example:
        ```
        GET /api/v1/rules/1
        ```
    """
    query = select(InstitutionalRule).where(InstitutionalRule.id == rule_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                "NOT_FOUND",
                f"Rule with id {rule_id} not found",
                404
            )
        )
    
    return rule


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: int,
    rule_update: RuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Update an institutional rule.
    
    **Permissions:** Admin only
    
    Args:
        rule_id: Rule ID
        rule_update: Updated rule data
        db: Database session
        current_admin: Current admin user
        
    Returns:
        RuleResponse: Updated rule
        
    Raises:
        404: Rule not found
        400: Invalid configuration
        
    Example:
        ```
        PUT /api/v1/rules/1
        {
            "weight": 0.8,
            "is_active": false
        }
        ```
    """
    query = select(InstitutionalRule).where(InstitutionalRule.id == rule_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                "NOT_FOUND",
                f"Rule with id {rule_id} not found",
                404
            )
        )
    
    # Validate configuration if provided
    if rule_update.configuration:
        try:
            _validate_rule_configuration(rule.rule_type, rule_update.configuration)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=create_error_response(
                    "INVALID_CONFIGURATION",
                    str(e),
                    400
                )
            )
    
    update_data = rule_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
    
    await db.commit()
    await db.refresh(rule)
    
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Delete an institutional rule.
    
    **Permissions:** Admin only
    
    Args:
        rule_id: Rule ID
        db: Database session
        current_admin: Current admin user
        
    Raises:
        404: Rule not found
        
    Example:
        ```
        DELETE /api/v1/rules/1
        ```
    """
    query = select(InstitutionalRule).where(InstitutionalRule.id == rule_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                "NOT_FOUND",
                f"Rule with id {rule_id} not found",
                404
            )
        )
    
    await db.delete(rule)
    await db.commit()
    
    return None


@router.patch("/{rule_id}/toggle", response_model=RuleResponse)
async def toggle_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Toggle rule active status (enable/disable).
    
    **Permissions:** Admin only
    
    Args:
        rule_id: Rule ID
        db: Database session
        current_admin: Current admin user
        
    Returns:
        RuleResponse: Updated rule
        
    Raises:
        404: Rule not found
        
    Example:
        ```
        PATCH /api/v1/rules/1/toggle
        ```
    """
    query = select(InstitutionalRule).where(InstitutionalRule.id == rule_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                "NOT_FOUND",
                f"Rule with id {rule_id} not found",
                404
            )
        )
    
    rule.is_active = not rule.is_active
    
    await db.commit()
    await db.refresh(rule)
    
    return rule


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def _validate_rule_configuration(rule_type: RuleType, config: dict) -> None:
    """
    Validate rule configuration based on rule type.
    
    Raises:
        ValueError: If configuration is invalid
    """
    if rule_type == RuleType.TIME_WINDOW:
        if "min_slot" not in config or "max_slot" not in config:
            raise ValueError("TIME_WINDOW requires 'min_slot' and 'max_slot'")
        if config["min_slot"] >= config["max_slot"]:
            raise ValueError("min_slot must be less than max_slot")
    
    elif rule_type == RuleType.SLOT_BLACKOUT:
        if "blackout_slots" not in config:
            raise ValueError("SLOT_BLACKOUT requires 'blackout_slots' list")
        if not isinstance(config["blackout_slots"], list):
            raise ValueError("blackout_slots must be a list")
    
    elif rule_type == RuleType.MAX_CONSECUTIVE:
        if "max_consecutive_classes" not in config:
            raise ValueError("MAX_CONSECUTIVE requires 'max_consecutive_classes'")
        if config["max_consecutive_classes"] < 1:
            raise ValueError("max_consecutive_classes must be >= 1")
    
    elif rule_type == RuleType.DAY_BLACKOUT:
        if "blackout_days" not in config:
            raise ValueError("DAY_BLACKOUT requires 'blackout_days' list")
        if not isinstance(config["blackout_days"], list):
            raise ValueError("blackout_days must be a list")
        if not all(0 <= day <= 6 for day in config["blackout_days"]):
            raise ValueError("blackout_days must contain values 0-6 (Monday-Sunday)")
    
    
    # Other rule types can have flexible configuration
