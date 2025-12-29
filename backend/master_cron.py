"""
Zero Interaction Attendance System - Master Cron Job
Processes sensor data to determine entry/exit events

SECURITY: Uses environment variables for credentials
Run as cron job at required frequency (e.g., every minute)

Author: Bishwa Bikash Das (Enhanced)
"""

import os
import sys
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Database configuration from environment variables
DB_CONFIG = {
    'user': os.getenv('DB_USER', 'IOT_master'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'database': os.getenv('DB_NAME', 'iot_data'),
    'port': int(os.getenv('DB_PORT', 3306))
}

# Configuration
TIME_WINDOW = int(os.getenv('TIME_WINDOW_SECONDS', 3))


def get_db_connection():
    """
    Create database connection with error handling
    
    Returns:
        connection: MySQL connection object or None
    """
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}", file=sys.stderr)
        return None


def process_sensor_data():
    """
    Process sensor data to identify entry/exit pairs
    Uses prepared statements to prevent SQL injection
    """
    con = get_db_connection()
    res_con = get_db_connection()
    
    if not con or not res_con:
        print("Failed to connect to database", file=sys.stderr)
        return
    
    try:
        cursor = con.cursor()
        res_cursor = res_con.cursor()
        res_con.autocommit = True
        
        # Query to find matching entry/exit pairs
        # Uses parameterized query to prevent SQL injection
        query = """
            SELECT DISTINCT 
                a.device_ID AS dev1,
                a.RFID + b.RFID AS RFID,
                a.time_stamp AS timestamp,
                a.cluster_ID AS cluster
            FROM sensor_data a, sensor_data b
            WHERE ABS(TIMESTAMPDIFF(SECOND, a.time_stamp, b.time_stamp)) < %s
                AND a.device_ID <> b.device_ID
                AND a.time_stamp < b.time_stamp
                AND a.cluster_ID = b.cluster_ID
        """
        
        cursor.execute(query, (TIME_WINDOW,))
        
        # Process results
        data_dict = {}
        
        for (dev1, rfid, timestamp, cluster) in cursor:
            # Determine entry (even device ID) vs exit (odd device ID)
            device_num = int(dev1[-1]) if dev1[-1].isdigit() else 0
            
            if device_num % 2 == 0:
                # Entry
                data_dict[rfid] = {'cluster': cluster, 'status': 1, 'timestamp': timestamp}
                print(f"Entry detected: RFID={rfid}, Cluster={cluster}")
            else:
                # Exit
                data_dict[rfid] = {'cluster': cluster, 'status': -1, 'timestamp': timestamp}
                print(f"Exit detected: RFID={rfid}, Cluster={cluster}")
        
        # Insert results into entry_log using prepared statements
        for rfid, data in data_dict.items():
            insert_query = """
                INSERT INTO entry_log (student_name, RFID, room_value, status, timestamp)
                VALUES (
                    (SELECT stud_name FROM student WHERE student.RFID = %s),
                    %s,
                    (SELECT DISTINCT room_value FROM user_devices WHERE cluster_ID = %s),
                    %s,
                    %s
                )
            """
            
            try:
                res_cursor.execute(insert_query, (
                    rfid,
                    rfid,
                    data['cluster'],
                    data['status'],
                    data['timestamp']
                ))
                print(f"Logged: RFID={rfid}, Status={data['status']}")
                
            except Error as e:
                print(f"Error inserting entry for RFID {rfid}: {e}", file=sys.stderr)
        
        print(f"Processed {len(data_dict)} events at {datetime.now()}")
        
    except Error as e:
        print(f"Database error: {e}", file=sys.stderr)
    
    finally:
        if cursor:
            cursor.close()
        if res_cursor:
            res_cursor.close()
        if con and con.is_connected():
            con.close()
        if res_con and res_con.is_connected():
            res_con.close()


if __name__ == "__main__":
    # Check if required environment variables are set
    if not DB_CONFIG['password']:
        print("ERROR: DB_PASSWORD environment variable not set!", file=sys.stderr)
        print("Please create .env file from .env.example", file=sys.stderr)
        sys.exit(1)
    
    process_sensor_data()
