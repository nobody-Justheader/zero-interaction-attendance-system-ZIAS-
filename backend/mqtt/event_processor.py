"""
Event Processor - Processes MQTT events and updates database
Runs as separate process/container
"""

import asyncio
import json
import redis.asyncio as redis
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from api.config import settings
from api.database import get_db_session
from api.db_models import SensorData, EntryLog, BLEEvent, Student, UserDevice


class EventProcessor:
    """Process sensor and BLE events from Redis"""
    
    def __init__(self):
        self.redis_client = None
        self.pubsub = None
        
    async def start(self):
        """Start event processor"""
        print("Starting event processor...")
        
        # Connect to Redis
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.pubsub = self.redis_client.pubsub()
        
        # Subscribe to event channel
        await self.pubsub.subscribe('zias:events')
        
        print(f"Subscribed to Redis channel: zias:events")
        print("Event processor ready!")
        
        # Process events
        async for message in self.pubsub.listen():
            if message['type'] == 'message':
                await self.process_event(message['data'])
    
    async def process_event(self, data: bytes):
        """Process individual event"""
        try:
            event = json.loads(data.decode())
            event_type = event.get('type')
            
            if event_type == 'sensor':
                await self.process_sensor_event(event)
            elif event_type == 'ble':
                await self.process_ble_event(event)
            else:
                print(f"Unknown event type: {event_type}")
                
        except Exception as e:
            print(f"Error processing event: {e}")
    
    async def process_sensor_event(self, event: dict):
        """Process RFID/PIR sensor event"""
        print(f"Processing sensor event: {event}")
        
        with get_db_session() as db:
            # Store raw sensor data
            sensor_data = SensorData(
                device_ID=event.get('device_id'),
                cluster_ID=event.get('cluster_id'),
                RFID=event.get('rfid'),
                sensor_active=event.get('sensor_active', True),
                time_stamp=datetime.fromisoformat(event.get('timestamp'))
            )
            db.add(sensor_data)
            
            # Check for matching entry/exit pair
            if event.get('rfid'):
                await self.check_entry_exit_match(db, event)
            
            db.commit()
    
    async def check_entry_exit_match(self, db: Session, event: dict):
        """
        Check if this event matches with a recent event from different device
        to determine entry vs exit
        """
        rfid = event.get('rfid')
        cluster_id = event.get('cluster_id')
        device_id = event.get('device_id')
        
        # Get recent events from same cluster but different device
        window_start = datetime.utcnow() - timedelta(seconds=settings.ATTENDANCE_WINDOW_SECONDS)
        
        recent_events = db.query(SensorData).filter(
            SensorData.cluster_ID == cluster_id,
            SensorData.RFID == rfid,
            SensorData.device_ID != device_id,
            SensorData.time_stamp >= window_start,
            SensorData.processed == False
        ).all()
        
        if recent_events:
            # Found matching event - determine entry vs exit
            # Device ID ending in even number = entry, odd = exit
            is_entry = int(device_id[-1]) % 2 == 0 if device_id[-1].isdigit() else True
            
            # Create entry log
            status = 1 if is_entry else -1
            
            # Get student name
            student = db.query(Student).filter(Student.RFID == rfid).first()
            student_name = student.stud_name if student else "Unknown"
            
            # Get room value
            device = db.query(UserDevice).filter(UserDevice.device_id == device_id).first()
            room = device.room_value if device else f"cluster_{cluster_id}"
            
            entry_log = EntryLog(
                student_name=student_name,
                RFID=rfid,
                room_value=room,
                status=status,
                confidence=0.95,
                source="rfid"
            )
            db.add(entry_log)
            
            # Mark events as processed
            for event in recent_events:
                event.processed = True
            
            print(f"Logged {'entry' if is_entry else 'exit'} for {student_name}")
    
    async def process_ble_event(self, event: dict):
        """Process BLE beacon event from mobile app"""
        print(f"Processing BLE event: {event}")
        
        with get_db_session() as db:
            # Store BLE event
            ble_event = BLEEvent(
                student_id=event.get('student_id'),
                beacon_uuid=event.get('beacon_uuid'),
                rssi=event.get('rssi'),
                latitude=event.get('location', {}).get('latitude'),
                longitude=event.get('location', {}).get('longitude'),
                event_type=event.get('event_type', 'unknown'),
                app_version=event.get('app_version', ''),
                timestamp=datetime.fromisoformat(event.get('timestamp'))
            )
            db.add(ble_event)
            
            # If entry/exit event, create attendance log
            if event.get('event_type') in ['entry', 'exit']:
                status = 1 if event.get('event_type') == 'entry' else -1
                
                student = db.query(Student).filter(Student.student_id == event.get('student_id')).first()
                
                if student:
                    # Extract room from beacon UUID (e.g., "zias-main-101-entry")
                    beacon_parts = event.get('beacon_uuid', '').split('-')
                    room = beacon_parts[2] if len(beacon_parts) > 2 else "unknown"
                    
                    entry_log = EntryLog(
                        student_name=student.stud_name,
                        RFID=student.RFID or '',
                        room_value=room,
                        status=status,
                        confidence=0.85,  # BLE slightly lower confidence than RFID
                        source="ble"
                    )
                    db.add(entry_log)
                    
                    print(f"Logged BLE {event.get('event_type')} for {student.stud_name}")
            
            db.commit()
    
    async def stop(self):
        """Stop event processor"""
        if self.pubsub:
            await self.pubsub.unsubscribe('zias:events')
        if self.redis_client:
            await self.redis_client.close()
        print("Event processor stopped")


async def main():
    """Main entry point"""
    processor = EventProcessor()
    
    try:
        await processor.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        await processor.stop()


if __name__ == "__main__":
    asyncio.run(main())
