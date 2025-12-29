"""Complete attendance API routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta

from api.models import AttendanceRecord, AttendanceEvent
from api.auth import get_current_user
from api.database import get_db
from api.db_models import EntryLog, Student, AttendanceSummary

router = APIRouter()


@router.post("/event", status_code=201)
async def log_attendance_event(
    event: AttendanceEvent,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log attendance event (used by mobile app)"""
    student = db.query(Student).filter(Student.student_id == event.student_id).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    status = 1 if event.event_type.value == "entry" else -1
    
    entry_log = EntryLog(
        student_name=student.stud_name,
        RFID=student.RFID or '',
        room_value=event.location,
        status=status,
        confidence=event.confidence,
        source=event.source.value
    )
    db.add(entry_log)
    db.commit()
    
    return {
        "status": "recorded",
        "event_id": entry_log.id,
        "student_id": event.student_id,
        "timestamp": entry_log.timestamp
    }


@router.get("/records", response_model=List[AttendanceRecord])
async def get_attendance_records(
    student_id: Optional[str] = None,
    room: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = Query(100, le=1000),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get attendance records with filters"""
    query = db.query(EntryLog).join(Student, EntryLog.RFID == Student.RFID)
    
    if student_id:
        query = query.filter(Student.student_id == student_id)
    if room:
        query = query.filter(EntryLog.room_value == room)
    if date_from:
        query = query.filter(EntryLog.timestamp >= date_from)
    if date_to:
        query = query.filter(EntryLog.timestamp <= date_to + timedelta(days=1))
    
    records = query.order_by(EntryLog.timestamp.desc()).limit(limit).all()
    
    result = []
    for record in records:
        student = db.query(Student).filter(Student.RFID == record.RFID).first()
        result.append(AttendanceRecord(
            id=record.id,
            student_id=student.student_id if student else "",
            student_name=record.student_name,
            room=record.room_value,
            entry_time=record.timestamp if record.status == 1 else None,
            exit_time=record.timestamp if record.status == -1 else None,
            duration_minutes=None,
            confidence=record.confidence
        ))
    
    return result


@router.get("/summary/{student_id}")
async def get_student_summary(
    student_id: str,
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get attendance summary for a student"""
    student = db.query(Student).filter(Student.student_id == student_id).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Calculate summary
    query = db.query(EntryLog).filter(EntryLog.RFID == student.RFID)
    
    if month and year:
        start_date = datetime(year, month, 1)
        end_date = start_date + timedelta(days=32)
        query = query.filter(
            EntryLog.timestamp >= start_date,
            EntryLog.timestamp < end_date
        )
    
    records = query.all()
    
    # Calculate stats
    entries = [r for r in records if r.status == 1]
    exits = [r for r in records if r.status == -1]
    
    total_hours = 0.0
    days_present = len(set(r.timestamp.date() for r in entries))
    
    return {
        "student_id": student_id,
        "student_name": student.stud_name,
        "total_hours": total_hours,
        "days_present": days_present,
        "total_entries": len(entries),
        "average_hours_per_day": total_hours / days_present if days_present > 0 else 0
    }


@router.get("/realtime/{room}")
async def get_realtime_occupancy(
    room: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get real-time room occupancy"""
    # Get latest status for each student in this room
    latest_entries = db.query(EntryLog).filter(
        EntryLog.room_value == room,
        EntryLog.timestamp >= datetime.utcnow() - timedelta(hours=12)
    ).order_by(EntryLog.timestamp.desc()).all()
    
    # Track who's currently inside
    student_status = {}
    for entry in latest_entries:
        if entry.RFID not in student_status:
            student_status[entry.RFID] = entry.status
    
    # Count those who entered but haven't exited
    current_occupancy = sum(1 for status in student_status.values() if status == 1)
    
    students_list = []
    for rfid, status in student_status.items():
        if status == 1:
            student = db.query(Student).filter(Student.RFID == rfid).first()
            if student:
                students_list.append({
                    "student_id": student.student_id,
                    "name": student.stud_name
                })
    
    return {
        "room": room,
        "current_occupancy": current_occupancy,
        "students": students_list,
        "timestamp": datetime.utcnow()
    }
