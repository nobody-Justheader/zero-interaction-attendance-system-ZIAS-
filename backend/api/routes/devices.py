"""Placeholder for device routes"""
from fastapi import APIRouter
router = APIRouter()

@router.get("/")
async def list_devices():
    return {"devices": []}
