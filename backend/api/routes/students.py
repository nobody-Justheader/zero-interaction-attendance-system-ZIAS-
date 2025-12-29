"""Placeholder for student routes"""
from fastapi import APIRouter
router = APIRouter()

@router.get("/")
async def list_students():
    return {"students": []}
