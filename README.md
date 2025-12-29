# Zero Interaction Attendance System (ZIAS)

Advanced IoT-based attendance tracking system using RFID and motion sensors for automatic, contactless attendance management.

## Features

- **Zero User Interaction**: Automatic detection via RFID and PIR sensors
- **Real-time Tracking**: Entry/exit detection with timestamp logging
- **Multi-room Support**: Cluster-based architecture for multiple locations
- **Database Backend**: MySQL storage with automated processing
- **IoT Integration**: ESP8266-based wireless sensor nodes

## System Architecture

```
┌─────────────┐     ┌─────────────┐
│ RFID Node   │────▶│             │
│ (ESP8266)   │     │   MySQL     │
└─────────────┘     │  Database   │
                    │             │
┌─────────────┐     │             │
│  PIR Node   │────▶│             │
│ (ESP8266)   │     └─────────────┘
└─────────────┘            │
                           │
                    ┌──────▼──────┐
                    │  Cron Job   │
                    │ (Python)    │
                    └─────────────┘
```

## Hardware Requirements

### RFID Node
- ESP8266 (NodeMCU)
- MFRC522 RFID Reader
- PIR Motion Sensor (HC-SR501)
- Power supply (5V)

### PIR Node  
- ESP8266 (NodeMCU)
- PIR Motion Sensor (HC-SR501)
- Power supply (5V)

## Software Requirements

- Arduino IDE (for ESP8266 programming)
- Python 3.8+
- MySQL Server 5.7+
- PHP 7.4+ (for backend API)

## Installation

### 1. Database Setup

```sql
CREATE DATABASE iot_data;
CREATE USER 'IOT_master'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON iot_data.* TO 'IOT_master'@'localhost';
FLUSH PRIVILEGES;
```

Run the schema file (see `docs/database_schema.sql`).

### 2. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your database credentials
```

### 3. Hardware Setup

#### Configure RFID Node
1. Open `hardware/rfid_node/rfid_node.ino` in Arduino IDE
2. Install required libraries:
   - MFRC522
   - ESP8266WiFi
   - ESP8266HTTPClient
3. Create `config.h` from `config.h.example`
4. Set your WiFi credentials and server IP
5. Upload to ESP8266

#### Configure PIR Node
1. Open `hardware/pir_node/pir_node.ino` in Arduino IDE
2. Create `config.h` from `config.h.example`
3. Set your WiFi credentials and server IP
4. Upload to ESP8266

### 4. Cron Job Setup

```bash
# Add to crontab (runs every minute)
crontab -e

# Add this line:
* * * * * /usr/bin/python3 /path/to/master_cron.py >> /var/log/zias.log 2>&1
```

## Configuration

All sensitive configuration is managed via environment variables. See `.env.example` for required variables:

```env
# Database
DB_HOST=localhost
DB_USER=IOT_master
DB_PASSWORD=your_secure_password
DB_NAME=iot_data

# API Server
API_HOST=10.10.0.4
API_PORT=80

# Device Configuration (per device)
WIFI_SSID=your_network
WIFI_PASSWORD=your_password
DEVICE_NAME=room1_PIR_1
CLUSTER_ID=1
```

## How It Works

1. **Entry Detection**: When a person enters a room:
   - Outer PIR sensor detects motion
   - RFID reader scans the ID card
   - Both events logged to database with timestamps

2. **Exit Detection**: When a person exits:
   - Inner PIR sensor detects motion
   - System correlates with RFID from entry
   - Exit event logged

3. **Processing**: Python cron job runs periodically:
   - Matches entry/exit pairs (within 3-second window)
   - Updates attendance log
   - Calculates time spent in room

## Database Schema

```sql
-- Sensor raw data
CREATE TABLE sensor_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_ID VARCHAR(50),
    cluster_ID INT,
    RFID VARCHAR(50),
    time_stamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sensor_active BOOLEAN
);

-- Student records
CREATE TABLE student (
    student_id VARCHAR(20) PRIMARY KEY,
    stud_name VARCHAR(100),
    RFID VARCHAR(50) UNIQUE
);

-- Attendance log
CREATE TABLE entry_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_name VARCHAR(100),
    RFID VARCHAR(50),
    room_value VARCHAR(50),
    status INT, -- 1=entry, -1=exit
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints

### POST /IOT/insert_data.php
Insert sensor data from IoT devices.

**Parameters**:
- `user_name`: Device identifier
- `cluster_id`: Room/cluster ID
- `device_DATA`: Sensor status
- `sensor`: Boolean (motion detected)
- `id`: RFID UID (optional, for RFID nodes)

## Security Considerations

**IMPORTANT**: This is a basic implementation. For production use:

- Use HTTPS/TLS for all communications
- Implement API authentication (JWT tokens)
- Use prepared statements to prevent SQL injection
- Store credentials in environment variables or secrets manager
- Enable WiFi encryption (WPA3)
- Implement device authentication
- Add rate limiting to API endpoints
- Regular security audits

## Troubleshooting

### ESP8266 won't connect to WiFi
- Check SSID and password in config.h
- Verify WiFi is 2.4GHz (ESP8266 doesn't support 5GHz)
- Check signal strength

### RFID not reading cards
- Verify SPI wiring (especially RST and SS pins)
- Check power supply (RFID needs stable 3.3V)
- Test with example MFRC522 library code

### Data not appearing in database
- Check PHP error logs
- Verify database credentials
- Test API endpoint with curl
- Check firewall rules

## Development

### Project Structure
```
ZIAS/
├── hardware/
│   ├── rfid_node/
│   │   ├── rfid_node.ino
│   │   └── config.h.example
│   ├── pir_node/
│   │   ├── pir_node.ino
│   │   └── config.h.example
│   └── schematics/
├── backend/
│   ├── master_cron.py
│   ├── requirements.txt
│   └── .env.example
├── docs/
│   └── database_schema.sql
├── .gitignore
├── LICENSE
└── README.md
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

GNU Affero General Public License v3.0

## Authors

Original concept and implementation by Bishwa Bikash Das

## Acknowledgments

- MFRC522 Library by Miguel Balboa
- ESP8266 Community
- Arduino Community

## Roadmap

- [ ] Web dashboard for attendance viewing
- [ ] Mobile app for students
- [ ] Real-time notifications
- [ ] Face recognition integration
- [ ] Cloud deployment support
- [ ] Multi-language support
- [ ] Export to CSV/PDF
- [ ] Analytics and reporting

## Support

For issues and feature requests, please use the GitHub issue tracker.

## Version

Current version: 1.0.0 (Enhanced)
