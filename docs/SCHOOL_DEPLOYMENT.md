# School-Wide Deployment Architecture for ZIAS

## Overview

This guide covers deploying ZIAS across an entire school with one central server detecting attendance from all classrooms.

## Hardware Placement Per Classroom

### Standard Configuration (2 Nodes Per Room)

```
                    [Classroom Door]
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
   [Node 1]                                [Node 2]
   Outside                                 Inside
   Entry Detection                         Exit Detection
        │                                     │
    ┌───┴────┐                           ┌───┴────┐
    │ ESP32  │                           │ ESP32  │
    │ RFID   │                           │ PIR    │
    │ PIR    │                           │        │
    └────────┘                           └────────┘
```

**Node 1 (Entry) - Outside classroom**:
- 1x ESP32
- 1x RFID reader (MFRC522)
- 1x PIR sensor
- Device name: `room101_entry`
- Cluster ID: 101

**Node 2 (Exit) - Inside classroom**:
- 1x ESP32  
- 1x PIR sensor (no RFID needed)
- Device name: `room101_exit`
- Cluster ID: 101

**Why 2 Nodes?**
- Determines direction (entry vs exit)
- Entry: PIR triggers → Student scans RFID
- Exit: PIR triggers → System knows they left
- Time window (10 seconds) matches entry+exit

### Cost Per Classroom

**Standard Setup** (2 nodes):
```
Entry Node:
- ESP32: Rs. 250
- RFID Reader: Rs. 150
- PIR Sensor: Rs. 100
- Enclosure/wiring: Rs. 100
Subtotal: Rs. 600

Exit Node:
- ESP32: Rs. 250
- PIR Sensor: Rs. 100
- Enclosure/wiring: Rs. 100
Subtotal: Rs. 450

Total per classroom: Rs. 1,050
```

**Budget Setup** (1 node):
```
Single Entry Node:
- ESP32: Rs. 250
- RFID Reader: Rs. 150
- PIR Sensor: Rs. 100
- Enclosure: Rs. 100
Total: Rs. 600

Note: Cannot detect exit, only entry
Use for: Roll call at class start only
```

## School-Wide Architecture

### Network Topology

```
                    ┌─────────────────┐
                    │  School Server  │
                    │  (Raspberry Pi) │
                    │    + MySQL      │
                    │    + MQTT       │
                    │    + Redis      │
                    └────────┬────────┘
                             │
                    [School WiFi Network]
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    [Classroom 1]       [Classroom 2]       [Classroom N]
         │                   │                   │
    ┌────┴────┐         ┌────┴────┐         ┌────┴────┐
    │ Node 1  │         │ Node 1  │         │ Node 1  │
    │ (Entry) │         │ (Entry) │         │ (Entry) │
    └─────────┘         └─────────┘         └─────────┘
         │                   │                   │
    ┌────┴────┐         ┌────┴────┐         ┌────┴────┐
    │ Node 2  │         │ Node 2  │         │ Node 2  │
    │ (Exit)  │         │ (Exit)  │         │ (Exit)  │
    └─────────┘         └─────────┘         └─────────┘
```

### Server Capacity

**Single Raspberry Pi 4 (4GB)** can handle:
- **50-100 classrooms** (100-200 nodes)
- **2,000-5,000 students**
- **10,000+ events per day**

**Server Specs**:
```
Hardware:
- Raspberry Pi 4 (4GB RAM): Rs. 6,000
- 500GB SSD: Rs. 3,000
- Case + Power: Rs. 1,000
- UPS (4 hour backup): Rs. 3,000
Total: Rs. 13,000

Software (all free/open-source):
- Raspberry Pi OS
- MySQL database
- Mosquitto MQTT broker
- Redis
- FastAPI backend
```

**When to Add Second Server**:
- More than 100 classrooms
- More than 5,000 students
- Multiple buildings far apart
- High availability requirement

## Deployment Examples

### Example 1: Small School (20 Classrooms)

**School Profile**:
- 20 classrooms
- 800 students
- 2 floors
- Single building

**Hardware**:
```
Nodes: 20 rooms × 2 nodes = 40 ESP32 nodes
Cost: 20 × Rs. 1,050 = Rs. 21,000

Server: 1 Raspberry Pi setup
Cost: Rs. 13,000

RFID Cards: 800 × Rs. 15 = Rs. 12,000

Total: Rs. 46,000
Per student: Rs. 57.50
```

**Network**:
- Single WiFi network
- One access point per floor
- All nodes connect to same server

### Example 2: Medium School (50 Classrooms)

**School Profile**:
- 50 classrooms
- 2,000 students
- 3 buildings
- Computer lab, library, auditorium

**Hardware**:
```
Classrooms: 50 × 2 nodes = 100 nodes
Special rooms: 5 × 2 nodes = 10 nodes
Total nodes: 110

Cost: 55 × Rs. 1,050 = Rs. 57,750

Server: 1 Raspberry Pi
Cost: Rs. 13,000

RFID Cards: 2,000 × Rs. 15 = Rs. 30,000

WiFi Access Points: 6 × Rs. 3,000 = Rs. 18,000

Total: Rs. 1,18,750
Per student: Rs. 59.37
```

**Network**:
- Multiple WiFi APs (one per building)
- Same network SSID
- Central server in admin building

### Example 3: Large School/College (100 Classrooms)

**School Profile**:
- 100 classrooms
- 4,000 students
- 5 buildings
- Labs, library, auditorium, cafeteria

**Hardware**:
```
Classrooms: 100 × 2 nodes = 200 nodes
Special areas: 20 × 2 nodes = 40 nodes
Total nodes: 240

Cost: 120 × Rs. 1,050 = Rs. 1,26,000

Server: 2 Raspberry Pi (redundancy)
Cost: 2 × Rs. 13,000 = Rs. 26,000

RFID Cards: 4,000 × Rs. 15 = Rs. 60,000

Network Infrastructure: Rs. 40,000

Total: Rs. 2,52,000
Per student: Rs. 63.00
```

**Network**:
- Multiple WiFi networks (one per building)
- Load balancing across 2 servers
- VPN link between buildings if needed

## Cluster ID Strategy

Each classroom gets a unique Cluster ID:

```
Building 1:
- Room 101: Cluster ID = 101
- Room 102: Cluster ID = 102
- Room 103: Cluster ID = 103

Building 2:
- Room 201: Cluster ID = 201
- Room 202: Cluster ID = 202

Labs:
- Computer Lab 1: Cluster ID = 501
- Physics Lab: Cluster ID = 502

Common Areas:
- Library: Cluster ID = 601
- Auditorium: Cluster ID = 602
```

**Device Naming Convention**:
```
Format: [location]_[type]_[number]

Examples:
- room101_entry_1
- room101_exit_1
- lab501_entry_1
- library_entry_1
```

## WiFi Network Requirements

### Bandwidth Per Node

**Typical MQTT Message**:
- Size: ~200 bytes
- Frequency: 1-2 per minute (during class hours)
- Bandwidth: <1 KB/minute per node

**100 Nodes**:
- Peak traffic: 100 KB/minute
- Average: 50 KB/minute
- **Negligible** on modern WiFi

**Recommendation**:
- 2.4GHz WiFi sufficient
- One AP per 50 nodes
- Standard school WiFi adequate

### WiFi Configuration

```
SSID: SCHOOL_IOT
Password: [Strong password]
Security: WPA2-PSK
Channel: Auto (avoid interference)
DHCP: Enabled
IP Range: 192.168.1.100-192.168.1.250
```

**Static IP for Server**:
```
Server IP: 192.168.1.10
Gateway: 192.168.1.1
DNS: 8.8.8.8
```

## Installation Timeline

### Week 1-2: Planning
- Survey all classrooms
- Decide cluster IDs
- Plan cable routing
- Order hardware

### Week 3-4: Infrastructure
- Install WiFi access points
- Setup server (Raspberry Pi)
- Configure network
- Test connectivity

### Week 5-8: Node Installation
- Install 10-15 nodes per day
- Configure each node
- Test MQTT connection
- Mount securely

### Week 9-10: Testing
- Test each classroom
- Enroll students
- Distribute RFID cards
- Train teachers

### Week 11-12: Rollout
- Start with 5 classrooms (pilot)
- Expand to full school
- Monitor and fix issues
- Optimize based on feedback

## Maintenance Requirements

### Daily
- Check server status (5 minutes)
- View dashboard for errors
- None if automated

### Weekly
- Review attendance reports
- Check offline nodes
- Clean RFID readers (if dusty)

### Monthly
- Database backup
- Software updates
- Battery replacement (if any)

### Annual
- Replace worn RFID cards
- Deep clean all sensors
- Hardware inspection

**Staff Required**:
- 1 computer teacher (part-time)
- No dedicated IT staff needed

## Scaling Strategy

### Start Small
1. **Pilot**: 5 classrooms (2 weeks)
2. **Expand**: Add 10 classrooms/week
3. **Complete**: Full school in 2-3 months

### Growth Path
```
Phase 1: 10 rooms (Rs. 20,000)
         ↓
Phase 2: 30 rooms (Rs. 50,000)
         ↓
Phase 3: 50 rooms (Rs. 80,000)
         ↓
Phase 4: 100 rooms (Rs. 1,50,000)
```

## Key Decisions Summary

**Q: How many PIR sensors per room?**  
**A**: 2 sensors (1 entry node + 1 exit node)

**Q: How many servers needed?**  
**A**: 1 Raspberry Pi for up to 100 classrooms

**Q: How many classrooms per server?**  
**A**: 50-100 classrooms (optimal: 50)

**Q: Can nodes be added incrementally?**  
**A**: Yes, add one room at a time

**Q: WiFi coverage needed?**  
**A**: Standard school WiFi sufficient

**Q: Internet required?**  
**A**: No, works offline (but nice to have)

## Cost Summary by School Size

| School Size | Rooms | Nodes | Server | RFID Cards | Total Cost | Per Student |
|-------------|-------|-------|--------|------------|------------|-------------|
| Small       | 20    | 40    | 1 Pi   | 800        | Rs. 46k    | Rs. 58      |
| Medium      | 50    | 110   | 1 Pi   | 2000       | Rs. 1.2L   | Rs. 60      |
| Large       | 100   | 240   | 2 Pi   | 4000       | Rs. 2.5L   | Rs. 63      |

**ROI**: Teacher time saved = 30 min/day × Rs. 500/hour = Rs. 250/day  
**Payback**: 6-12 months depending on size

## Recommended Configuration

For most Indian schools (500-1000 students):
- **30-40 classrooms** × 2 nodes = 60-80 ESP32 nodes
- **1 Raspberry Pi 4** server
- **1,000 RFID cards**
- **Total: Rs. 80,000 to Rs. 1,00,000**
- **Per student: Rs. 60-80**

Start with 5 classrooms, expand based on success.
