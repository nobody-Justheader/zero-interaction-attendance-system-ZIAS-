# BLE Beacon Configuration for ZIAS

## Overview

This document describes the BLE beacon deployment strategy for smartphone-based attendance tracking as a complement to RFID/PIR sensors.

## Hardware: BLE Beacons

### Recommended Beacons

**Option 1: iBeacon Compatible** (iOS + Android)
- Estimote Beacons
- Kontakt.io Beacons
- Cost: $20-40 per beacon

**Option 2: Eddystone** (Google standard)
- Better for Android
- Open source
- Cost: $15-30 per beacon

### Beacon Placement

```
[Room 101]
    ↓
┌─────────────┐
│  Entrance   │  ← BLE Beacon #1 (UUID: room-101-entry)
├─────────────┤
│             │
│    Room     │  ← BLE Beacon #2 (UUID: room-101-inside) 
│             │
├─────────────┤
│    Exit     │  ← BLE Beacon #3 (UUID: room-101-exit)
└─────────────┘
```

**Placement Rules**:
- Entry beacon: 1m inside entrance
- Inside beacon: Center of room
- Exit beacon: 1m before exit
- Range: 2-5 meters configured
- Height: 2-2.5 meters

## UUID Naming Convention

```
Entry: zias-{building}-{room}-entry
Inside: zias-{building}-{room}-inside
Exit: zias-{building}-{room}-exit

Example:
- zias-main-101-entry
- zias-main-101-inside
- zias-main-101-exit
```

## Mobile App Detection Logic

### State Machine

```
OUTSIDE → [Detect entry beacon] → APPROACHING
APPROACHING → [Detect inside beacon] → INSIDE
INSIDE → [Detect exit beacon] → LEAVING
LEAVING → [Lost all beacons] → OUTSIDE
```

### Geofencing Rules

```python
# Pseudo-code
if beacon.rssi > -60:  # Strong signal (< 2m)
    student_is_near_beacon = True
elif beacon.rssi > -75:  # Medium signal (2-5m)
    student_is_medium_distance = True
else:  # Weak signal (> 5m)
    ignore_beacon = True
```

### Detection Algorithm

```javascript
// Mobile app logic
let state = 'OUTSIDE';
let entryTime = null;

function onBeaconDetected(beacon) {
    switch(state) {
        case 'OUTSIDE':
            if (beacon.uuid.includes('entry') && beacon.rssi > -70) {
                state = 'APPROACHING';
                notifyServer({ event: 'approaching', beacon: beacon.uuid });
            }
            break;
            
        case 'APPROACHING':
            if (beacon.uuid.includes('inside') && beacon.rssi > -65) {
                state = 'INSIDE';
                entryTime = Date.now();
                notifyServer({ 
                    event: 'entry', 
                    beacon: beacon.uuid,
                    timestamp: entryTime 
                });
            }
            break;
            
        case 'INSIDE':
            if (beacon.uuid.includes('exit') && beacon.rssi > -70) {
                state = 'LEAVING';
                const duration = Date.now() - entryTime;
                notifyServer({ 
                    event: 'exit', 
                    beacon: beacon.uuid,
                    duration: duration 
                });
            }
            break;
            
        case 'LEAVING':
            if (allBeaconsLost()) {
                state = 'OUTSIDE';
            }
            break;
    }
}
```

## Mobile App Requirements

### Features

1. **Background Scanning**
   - Continuous BLE scanning even when app closed
   - Battery-efficient (use region monitoring)

2. **Geofencing**
   - Verify GPS coordinates match room location
   - Prevent spoofing from outside campus

3. **Notifications**
   - "Attendance marked for Room 101"
   - "You exited Room 101 - Duration: 45 minutes"

4. **Offline Support**
   - Queue events when offline
   - Sync when connection restored

### Tech Stack

**Option 1: Flutter** (Recommended)
- Cross-platform (iOS + Android)
- `flutter_beacon` plugin
- `geolocator` for geofencing

**Option 2: React Native**
- `react-native-beacons-manager`
- Large community

**Option 3: Native**
- Best performance
- Requires separate iOS/Android codebases

## API Integration

### MQTT Topics

```
zias/mobile/{student_id}/beacon
```

### Payload Format

```json
{
    "student_id": "ST001",
    "beacon_uuid": "zias-main-101-entry",
    "rssi": -65,
    "event_type": "entry|exit|approaching",
    "location": {
        "latitude": 12.9716,
        "longitude": 77.5946
    },
    "timestamp": "2025-12-29T11:45:00Z",
    "app_version": "1.0.0"
}
```

## Security Considerations

### Anti-Spoofing

1. **Geofencing Validation**
   ```python
   if distance(student_gps, room_gps) > 100_meters:
       reject_attendance()  # Too far away
   ```

2. **Beacon Rotation**
   - Change beacon UUIDs weekly
   - Distribute via app update

3. **RSSI Validation**
   - Reject if RSSI indicates impossible distance
   - Check for signal consistency

4. **App Attestation**
   - Verify app is legitimate (not modded)
   - Use SafetyNet (Android) / DeviceCheck (iOS)

### Privacy

- No tracking when not on campus
- Clear data retention policy
- Opt-in for location services
- GDPR/privacy law compliance

## Hybrid System: RFID + BLE

### Priority Logic

```python
def record_attendance(event):
    if event.source == 'rfid':
        # Primary method - highest confidence
        confidence = 0.95
        log_attendance(event, confidence)
    
    elif event.source == 'ble':
        # Check if RFID also detected
        recent_rfid = check_recent_rfid(event.student_id, window=10s)
        
        if recent_rfid:
            # Both methods agree - very high confidence
            confidence = 0.99
        else:
            # BLE only - good confidence
            confidence = 0.85
        
        log_attendance(event, confidence)
```

### Redundancy Benefits

- BLE works if student forgets card
- RFID works if student's phone is dead
- Cross-validation prevents fraud
- Higher system reliability

## Deployment Checklist

### Hardware
- [ ] Purchase BLE beacons (3 per room)
- [ ] Configure beacon UUIDs
- [ ] Test beacon range and placement
- [ ] Mount beacons at correct height

### Software
- [ ] Build mobile app (Flutter)
- [ ] Implement background scanning
- [ ] Add geofencing logic
- [ ] Test on iOS and Android
- [ ] Submit to App Store / Play Store

### Backend
- [ ] Update MQTT topics for BLE
- [ ] Add BLE event processing
- [ ] Create student app API
- [ ] Implement anti-spoofing checks

### Testing
- [ ] Test entry/exit detection
- [ ] Verify geofencing accuracy
- [ ] Check battery consumption
- [ ] Load test with multiple users

## Cost Estimate

| Item | Qty | Unit Cost | Total |
|------|-----|-----------|-------|
| BLE Beacons | 30 | $25 | $750 |
| Mobile App Development | 1 | $2000 | $2000 |
| Backend Updates | 1 | $500 | $500 |
| **Total** | | | **$3,250** |

Plus ongoing: App Store fees ($100/year)

## Timeline

- Week 1: Beacon procurement and setup
- Week 2-3: Mobile app development
- Week 4: Backend integration
- Week 5: Testing and deployment
- Week 6: User training and rollout

Total: 6 weeks for full BLE system
