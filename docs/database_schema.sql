-- Zero Interaction Attendance System (ZIAS) Database Schema
-- MySQL 5.7+ compatible schema

-- Drop existing tables if they exist (careful in production!)
DROP TABLE IF EXISTS entry_log;
DROP TABLE IF EXISTS sensor_data;
DROP TABLE IF EXISTS student;
DROP TABLE IF EXISTS user_devices;

-- Student master table
CREATE TABLE student (
    student_id VARCHAR(20) PRIMARY KEY,
    stud_name VARCHAR(100) NOT NULL,
    RFID VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_rfid (RFID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Device configuration table
CREATE TABLE user_devices (
    device_id VARCHAR(50) PRIMARY KEY,
    cluster_ID INT NOT NULL,
    device_type ENUM('rfid', 'pir') NOT NULL,
    room_value VARCHAR(50) NOT NULL,
    location_description VARCHAR(200),
    last_seen TIMESTAMP NULL,
    status ENUM('active', 'inactive', 'maintenance') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_cluster (cluster_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Raw sensor data table
CREATE TABLE sensor_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_ID VARCHAR(50) NOT NULL,
    cluster_ID INT NOT NULL,
    RFID VARCHAR(50),
    time_stamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sensor_active BOOLEAN DEFAULT TRUE,
    processed BOOLEAN DEFAULT FALSE,
    INDEX idx_timestamp (time_stamp),
    INDEX idx_cluster (cluster_ID),
    INDEX idx_device (device_ID),
    INDEX idx_rfid (RFID),
    INDEX idx_processed (processed),
    FOREIGN KEY (device_ID) REFERENCES user_devices(device_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Entry/exit log table
CREATE TABLE entry_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_name VARCHAR(100),
    RFID VARCHAR(50) NOT NULL,
    room_value VARCHAR(50),
    status INT NOT NULL COMMENT '1=entry, -1=exit',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_rfid (RFID),
    INDEX idx_timestamp (timestamp),
    INDEX idx_room (room_value),
    FOREIGN KEY (RFID) REFERENCES student(RFID) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Attendance summary table (for quick reporting)
CREATE TABLE attendance_summary (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    total_hours DECIMAL(5,2) DEFAULT 0,
    first_entry TIME,
    last_exit TIME,
    entry_count INT DEFAULT 0,
    UNIQUE KEY unique_student_date (student_id, date),
    INDEX idx_date (date),
    FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert sample data for testing

-- Sample students
INSERT INTO student (student_id, stud_name, RFID, email) VALUES
('ST001', 'John Doe', '04 AB CD EF', 'john.doe@example.com'),
('ST002', 'Jane Smith', '12 34 56 78', 'jane.smith@example.com'),
('ST003', 'Bob Johnson', 'AB CD EF 01', 'bob.johnson@example.com');

-- Sample devices
INSERT INTO user_devices (device_id, cluster_ID, device_type, room_value, location_description, status) VALUES
('room1_PIR_1', 1, 'pir', 'room_101', 'Room 101 - Outer PIR Sensor', 'active'),
('room1_PIR_2', 1, 'pir', 'room_101', 'Room 101 - Inner PIR Sensor', 'active'),
('room1_RFID_1', 1, 'rfid', 'room_101', 'Room 101 - Entry RFID Reader', 'active'),
('room2_PIR_1', 2, 'pir', 'room_102', 'Room 102 - Outer PIR Sensor', 'active'),
('room2_PIR_2', 2, 'pir', 'room_102', 'Room 102 - Inner PIR Sensor', 'active');

-- Trigger to auto-update attendance summary
DELIMITER $$

CREATE TRIGGER update_attendance_summary
AFTER INSERT ON entry_log
FOR EACH ROW
BEGIN
    DECLARE student_id_var VARCHAR(20);
    DECLARE date_var DATE;
    
    -- Get student_id from RFID
    SELECT student.student_id INTO student_id_var
    FROM student
    WHERE student.RFID = NEW.RFID;
    
    SET date_var = DATE(NEW.timestamp);
    
    -- Update or insert summary
    INSERT INTO attendance_summary (student_id, date, entry_count, first_entry, last_exit)
    VALUES (
        student_id_var,
        date_var,
        1,
        CASE WHEN NEW.status = 1 THEN TIME(NEW.timestamp) ELSE NULL END,
        CASE WHEN NEW.status = -1 THEN TIME(NEW.timestamp) ELSE NULL END
    )
    ON DUPLICATE KEY UPDATE
        entry_count = entry_count + 1,
        first_entry = CASE 
            WHEN NEW.status = 1 AND (first_entry IS NULL OR TIME(NEW.timestamp) < first_entry)
            THEN TIME(NEW.timestamp)
            ELSE first_entry
        END,
        last_exit = CASE
            WHEN NEW.status = -1 AND (last_exit IS NULL OR TIME(NEW.timestamp) > last_exit)
            THEN TIME(NEW.timestamp)
            ELSE last_exit
        END,
        total_hours = CASE
            WHEN first_entry IS NOT NULL AND last_exit IS NOT NULL
            THEN TIMESTAMPDIFF(SECOND, first_entry, last_exit) / 3600
            ELSE total_hours
        END;
END$$

DELIMITER ;

-- Useful queries for reporting

-- Daily attendance report
-- SELECT 
--     s.student_id,
--     s.stud_name,
--     a.date,
--     a.first_entry,
--     a.last_exit,
--     a.total_hours,
--     a.entry_count
-- FROM attendance_summary a
-- JOIN student s ON a.student_id = s.student_id
-- WHERE a.date = CURDATE()
-- ORDER BY s.stud_name;

-- Current occupancy by room
-- SELECT 
--     e.room_value,
--     COUNT(DISTINCT e.RFID) as current_occupants
-- FROM entry_log e
-- WHERE e.id IN (
--     SELECT MAX(id)
--     FROM entry_log
--     GROUP BY RFID, room_value
-- )
-- AND e.status = 1
-- GROUP BY e.room_value;
