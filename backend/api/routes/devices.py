"""Devices API routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from api.models import DeviceRegister
from api.auth import get_current_user
from api.database import get_db
from api.db_models import UserDevice, DeviceTypeEnum, DeviceStatusEnum

router = APIRouter()


@router.get("/")
async def list_devices(
    cluster_id: int = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all devices"""
    query = db.query(UserDevice)
    
    if cluster_id is not None:
        query = query.filter(UserDevice.cluster_ID == cluster_id)
    
    devices = query.all()
    
    return {
        "devices": [
            {
                "device_id": d.device_id,
                "cluster_id": d.cluster_ID,
                "device_type": d.device_type.value,
                "room": d.room_value,
                "has_rfid": d.has_rfid,
                "has_pir": d.has_pir,
                "has_ble": d.has_ble,
                "status": d.status.value,
                "last_seen": d.last_seen,
                "ip": d.ip_address
            }
            for d in devices
        ]
    }


@router.post("/register", status_code=201)
async def register_device(
    device: DeviceRegister,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register new device"""
    existing = db.query(UserDevice).filter(UserDevice.device_id == device.device_id).first()
    
    if existing:
        # Update existing device
        existing.cluster_ID = device.cluster_id
        existing.device_type = device.device_type
        existing.room_value = device.room_value
        existing.location_description = device.location_description
        existing.last_seen = datetime.utcnow()
        db.commit()
        
        return {"message": "Device updated", "device_id": device.device_id}
    
    # Create new device
    db_device = UserDevice(
        device_id=device.device_id,
        cluster_ID=device.cluster_id,
        device_type=device.device_type,
        room_value=device.room_value,
        location_description=device.location_description,
        status=DeviceStatusEnum.ACTIVE
    )
    db.add(db_device)
    db.commit()
    
    return {"message": "Device registered", "device_id": device.device_id}


@router.post("/{device_id}/heartbeat")
async def device_heartbeat(
    device_id: str,
    has_rfid: bool = False,
    has_pir: bool = False,
    has_ble: bool = False,
    ip_address: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update device heartbeat and capabilities"""
    device = db.query(UserDevice).filter(UserDevice.device_id == device_id).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device.last_seen = datetime.utcnow()
    device.has_rfid = has_rfid
    device.has_pir = has_pir
    device.has_ble = has_ble
    device.ip_address = ip_address
    device.status = DeviceStatusEnum.ACTIVE
    
    db.commit()
    
    return {"status": "updated", "device_id": device_id}
