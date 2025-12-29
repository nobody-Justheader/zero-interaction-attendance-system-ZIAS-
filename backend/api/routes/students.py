"""Students API routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from api.models import Student as StudentModel, StudentCreate
from api.auth import get_current_user
from api.database import get_db
from api.db_models import Student

router = APIRouter()


@router.get("/", response_model=List[StudentModel])
async def list_students(
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all students"""
    students = db.query(Student).limit(limit).all()
    return students


@router.post("/", response_model=StudentModel, status_code=201)
async def create_student(
    student: StudentCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new student"""
    # Check if student_id already exists
    existing = db.query(Student).filter(Student.student_id == student.student_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student ID already exists")
    
    db_student = Student(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    
    return db_student


@router.get("/{student_id}", response_model=StudentModel)
async def get_student(
    student_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get student by ID"""
    student = db.query(Student).filter(Student.student_id == student_id).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return student
