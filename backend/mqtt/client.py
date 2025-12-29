"""
MQTT Client for handling IoT device events
Publishes to Redis and processes attendance logic
"""

import paho.mqtt.client as mqtt
import json
import asyncio
from datetime import datetime
from typing import Dict, Any
import redis.asyncio as redis

from api.config import settings
from api.models import AttendanceEvent, DeviceType


class MQTTClient:
    """MQTT client for device communication"""
    
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        self.redis_client = None
        self.connected = False
        
        if settings.MQTT_USERNAME:
            self.client.username_pw_set(
                settings.MQTT_USERNAME,
                settings.MQTT_PASSWORD
            )
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            print(f"Connected to MQTT broker at {settings.MQTT_BROKER}")
            self.connected = True
            
            # Subscribe to all device topics
            topics = [
                f"{settings.MQTT_TOPIC_PREFIX}/devices/+/sensor",  # RFID/PIR events
                f"{settings.MQTT_TOPIC_PREFIX}/mobile/+/beacon",   # BLE events
                f"{settings.MQTT_TOPIC_PREFIX}/devices/+/status",  # Device status
            ]
            
            for topic in topics:
                client.subscribe(topic)
                print(f"Subscribed to: {topic}")
        else:
            print(f"Failed to connect to MQTT broker, code: {rc}")
            self.connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected"""
        print(f"Disconnected from MQTT broker, code: {rc}")
        self.connected = False
    
    def on_message(self, client, userdata, msg):
        """Callback when message received"""
        try:
            payload = json.loads(msg.payload.decode())
            topic_parts = msg.topic.split('/')
            
            if 'sensor' in msg.topic:
                # RFID/PIR sensor event
                self.handle_sensor_event(topic_parts[2], payload)
            elif 'beacon' in msg.topic:
                # BLE beacon event from mobile app
                self.handle_beacon_event(topic_parts[2], payload)
            elif 'status' in msg.topic:
                # Device status update
                self.handle_device_status(topic_parts[2], payload)
                
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in MQTT message: {e}")
        except Exception as e:
            print(f"Error processing MQTT message: {e}")
    
    def handle_sensor_event(self, device_id: str, payload: Dict[str, Any]):
        """Handle RFID/PIR sensor events"""
        print(f"Sensor event from {device_id}: {payload}")
        
        # Publish to Redis for real-time processing
        asyncio.create_task(self.publish_to_redis({
            'type': 'sensor',
            'device_id': device_id,
            'rfid': payload.get('id'),
            'cluster_id': payload.get('cluster_id'),
            'sensor_active': payload.get('sensor', False),
            'timestamp': datetime.utcnow().isoformat()
        }))
    
    def handle_beacon_event(self, student_id: str, payload: Dict[str, Any]):
        """Handle BLE beacon events from smartphone app"""
        print(f"BLE beacon event from {student_id}: {payload}")
        
        asyncio.create_task(self.publish_to_redis({
            'type': 'ble',
            'student_id': student_id,
            'beacon_uuid': payload.get('beacon_uuid'),
            'rssi': payload.get('rssi'),
            'location': payload.get('location'),
            'timestamp': datetime.utcnow().isoformat()
        }))
    
    def handle_device_status(self, device_id: str, payload: Dict[str, Any]):
        """Handle device status updates"""
        print(f"Device status from {device_id}: {payload}")
        
        # Update device last_seen in database
        asyncio.create_task(self.update_device_status(device_id, payload))
    
    async def publish_to_redis(self, event: Dict[str, Any]):
        """Publish event to Redis for processing"""
        if not self.redis_client:
            self.redis_client = redis.from_url(settings.REDIS_URL)
        
        # Publish to Redis channel for real-time processing
        await self.redis_client.publish(
            'zias:events',
            json.dumps(event)
        )
        
        # Also store in Redis with TTL for state tracking
        key = f"zias:state:{event.get('device_id', event.get('student_id'))}"
        await self.redis_client.setex(
            key,
            settings.ATTENDANCE_WINDOW_SECONDS,
            json.dumps(event)
        )
    
    async def update_device_status(self, device_id: str, status: Dict[str, Any]):
        """Update device status in database"""
        # TODO: Implement database update
        pass
    
    def publish(self, topic: str, payload: Dict[str, Any]):
        """Publish message to MQTT topic"""
        self.client.publish(
            f"{settings.MQTT_TOPIC_PREFIX}/{topic}",
            json.dumps(payload)
        )
    
    def start(self):
        """Start MQTT client"""
        try:
            self.client.connect(
                settings.MQTT_BROKER,
                settings.MQTT_PORT,
                keepalive=60
            )
            self.client.loop_start()
            print("MQTT client started")
        except Exception as e:
            print(f"Failed to start MQTT client: {e}")
    
    def stop(self):
        """Stop MQTT client"""
        self.client.loop_stop()
        self.client.disconnect()
        print("MQTT client stopped")
    
    def is_connected(self) -> bool:
        """Check if connected to broker"""
        return self.connected


# Global MQTT client instance
mqtt_client = MQTTClient()
