"""
SQLAlchemy database models for ZIAS
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class DeviceTypeEnum(enum.Enum):
    RFID = "rfid"
    PIR = "pir"
    BLE_BEACON = "ble_beacon"
    UNIVERSAL = "universal"


class DeviceStatusEnum(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class Student(Base):
    __tablename__ = "student"
    
    student_id = Column(String(20), primary_key=True)
    stud_name = Column(String(100), nullable=False)
    RFID = Column(String(50), unique=True, nullable=True, index=True)
    email = Column(String(100))
    phone = Column(String(15))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attendance_logs = relationship("EntryLog", back_populates="student")


class UserDevice(Base):
    __tablename__ = "user_devices"
    
    device_id = Column(String(50), primary_key=True)
    cluster_ID = Column(Integer, nullable=False, index=True)
    device_type = Column(Enum(DeviceTypeEnum), nullable=False)
    room_value = Column(String(50), nullable=False, index=True)
    location_description = Column(String(200))
    has_rfid = Column(Boolean, default=False)
    has_pir = Column(Boolean, default=False)
    has_ble = Column(Boolean, default=False)
    ip_address = Column(String(15))
    last_seen = Column(DateTime)
    status = Column(Enum(DeviceStatusEnum), default=DeviceStatusEnum.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sensor_data = relationship("SensorData", back_populates="device")


class SensorData(Base):
    __tablename__ = "sensor_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_ID = Column(String(50), ForeignKey("user_devices.device_id"), nullable=False, index=True)
    cluster_ID = Column(Integer, nullable=False, index=True)
    RFID = Column(String(50), index=True)
    time_stamp = Column(DateTime, default=datetime.utcnow, index=True)
    sensor_active = Column(Boolean, default=True)
    processed = Column(Boolean, default=False, index=True)
    
    # Relationships
    device = relationship("UserDevice", back_populates="sensor_data")


class EntryLog(Base):
    __tablename__ = "entry_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_name = Column(String(100))
    RFID = Column(String(50), ForeignKey("student.RFID"), nullable=False, index=True)
    room_value = Column(String(50), index=True)
    status = Column(Integer, nullable=False)  # 1=entry, -1=exit
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    confidence = Column(Float, default=1.0)  # Confidence score (0-1)
    source = Column(String(20), default="rfid")  # rfid, ble, face
    
    # Relationships
    student = relationship("Student", back_populates="attendance_logs")


class AttendanceSummary(Base):
    __tablename__ = "attendance_summary"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(20), ForeignKey("student.student_id"), nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    total_hours = Column(Float, default=0.0)
    first_entry = Column(DateTime)
    last_exit = Column(DateTime)
    entry_count = Column(Integer, default=0)
    
    # Unique constraint
    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'},
    )


class BLEEvent(Base):
    __tablename__ = "ble_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(20), ForeignKey("student.student_id"), nullable=False)
    beacon_uuid = Column(String(100), nullable=False, index=True)
    rssi = Column(Integer)  # Signal strength
    latitude = Column(Float)
    longitude = Column(Float)
    event_type = Column(String(20))  # entry, exit, approaching
    app_version = Column(String(20))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    processed = Column(Boolean, default=False, index=True)
