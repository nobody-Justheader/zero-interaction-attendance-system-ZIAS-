"""
Pydantic models for API requests/responses
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class DeviceType(str, Enum):
    RFID = "rfid"
    PIR = "pir"
    BLE_BEACON = "ble_beacon"


class EventType(str, Enum):
    ENTRY = "entry"
    EXIT = "exit"
    APPROACHING = "approaching"


class AttendanceEvent(BaseModel):
    """Attendance event from any source"""
    student_id: str
    event_type: EventType
    source: DeviceType
    location: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    metadata: Optional[dict] = None


class BeaconEvent(BaseModel):
    """BLE beacon detection event"""
    student_id: str
    beacon_uuid: str
    rssi: int
    location: dict  # {latitude, longitude}
    event_type: EventType
    app_version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AttendanceRecord(BaseModel):
    """Attendance record for response"""
    id: int
    student_id: str
    student_name: str
    room: str
    entry_time: datetime
    exit_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    confidence: float


class StudentCreate(BaseModel):
    """Create student"""
    student_id: str
    name: str
    rfid_uid: Optional[str] = None
    email: Optional[str] = None


class Student(StudentCreate):
    """Student response"""
    created_at: datetime


class DeviceRegister(BaseModel):
    """Register new device"""
    device_id: str
    device_type: DeviceType
    cluster_id: int
    room_value: str
    location_description: Optional[str] = None


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload"""
    username: Optional[str] = None
