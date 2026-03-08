from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal


class RoomBase(BaseModel):
    """Base Room schema - with split building/room_number/full_name"""
    building: str = Field(..., min_length=1, max_length=50, examples=["ABIII"])
    room_number: str = Field(..., min_length=1, max_length=50, examples=["C302"])
    full_name: str = Field(..., min_length=1, max_length=100, examples=["ABIII - C302"])
    room_type: Literal['classroom', 'lab', 'auditorium', 'seminar_hall'] = Field(..., examples=["classroom"])
    capacity: int = Field(..., gt=0, examples=[60])
    has_projector: bool = Field(default=False)
    has_lab_equipment: bool = Field(default=False)
    has_ac: bool = Field(default=False)
    floor: Optional[int] = Field(None, examples=[3])
    location_x: Optional[float] = Field(None, examples=[100.5])
    location_y: Optional[float] = Field(None, examples=[50.3])


class RoomCreate(RoomBase):
    """Schema for creating a room"""
    pass


class RoomUpdate(BaseModel):
    """Schema for updating a room"""
    building: Optional[str] = Field(None, min_length=1, max_length=50)
    room_number: Optional[str] = Field(None, min_length=1, max_length=50)
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    room_type: Optional[Literal['classroom', 'lab', 'auditorium', 'seminar_hall']] = None
    capacity: Optional[int] = Field(None, gt=0)
    has_projector: Optional[bool] = None
    has_lab_equipment: Optional[bool] = None
    has_ac: Optional[bool] = None
    floor: Optional[int] = None
    location_x: Optional[float] = None
    location_y: Optional[float] = None


class RoomResponse(RoomBase):
    """Schema for room responses"""
    id: int
    
    model_config = ConfigDict(from_attributes=True)


class RoomListResponse(BaseModel):
    """Schema for listing rooms"""
    data: list[RoomResponse]
    total: int
