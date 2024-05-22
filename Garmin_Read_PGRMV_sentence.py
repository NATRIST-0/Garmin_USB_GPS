#!/usr/bin/env python3
# author: Tristan Gayrard

"""
Garmin_Read_PGRMV_sentence, after activation
"""

import serial
from datetime import datetime

ser = serial.Serial(
    port='COM9', 
    baudrate=4800,        
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

def read_gps_data():
    while True:
        try:
            line = ser.readline().decode('ascii', errors='replace').strip()
            if line:
                if line.startswith('$PGRMV'):
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    parse_pgrmv(line, timestamp)
        except serial.SerialException as e:
            print(f"Serial error: {e}")
        except KeyboardInterrupt:
            print("Exiting...")
            ser.close()
            print("Serial port closed")
            break

def parse_pgrmv(data, timestamp):
    # $PGRMV,<True east velocity>,<True north velocity>,<Up velocity>*hh
    parts = data.split(',')
    if len(parts) < 4:
        print("Invalid PGRMV data")
        return

    try:
        true_east_velocity = float(parts[1])
        true_north_velocity = float(parts[2])
        up_velocity = float(parts[3].split('*')[0])  # Extraire la valeur avant le checksum

        print(f"Timestamp: {timestamp}")
        print(f"True East Velocity: {true_east_velocity} m/s")
        print(f"True North Velocity: {true_north_velocity} m/s")
        print(f"Up Velocity: {up_velocity} m/s\n")
    except ValueError as e:
        print(f"Error parsing PGRMV data: {e}")

if __name__ == "__main__":
    read_gps_data()
