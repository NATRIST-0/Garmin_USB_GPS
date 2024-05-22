#!/usr/bin/env python3
# author: Tristan Gayrard

"""
Garmin_Read_PGRMV_sentence, after activation
"""

import serial
from datetime import datetime
import pandas as pd

ser = serial.Serial(
    port='COM9', 
    baudrate=4800,        
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

# making empty dataframes to store all values
df = pd.DataFrame(columns=['Timestamp', 'True East Velocity', 'True North Velocity', 'Up Velocity', 
                           'Position X', 'Position Y', 'Position Z'])

def read_gps_data():
    last_timestamp = None
    last_position = [0, 0, 0]  # initial position

    while True:
        try:
            line = ser.readline().decode('ascii', errors='replace').strip()
            if line:
                if line.startswith('$PGRMV'):
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    parse_pgrmv(line, timestamp, last_timestamp, last_position)
                    last_timestamp = timestamp
        except serial.SerialException as e:
            print(f"Serial error: {e}")
        except KeyboardInterrupt:
            print("Exiting...")
            ser.close()
            print("Serial port closed")
            break

def parse_pgrmv(data, timestamp, last_timestamp, last_position):
    # $PGRMV,<True east velocity>,<True north velocity>,<Up velocity>*hh
    parts = data.split(',')
    if len(parts) < 4:
        print("Invalid PGRMV data")
        return

    try:
        true_east_velocity = float(parts[1])
        true_north_velocity = float(parts[2])
        up_velocity = float(parts[3].split('*')[0])

        # calculation of position in fonction of speed
        delta_t = 0
        if last_timestamp:
            delta_t = (datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S') - 
                       datetime.strptime(last_timestamp, '%Y-%m-%d %H:%M:%S')).total_seconds()

        delta_x = true_east_velocity * delta_t
        delta_y = true_north_velocity * delta_t
        delta_z = up_velocity * delta_t

        # calculations of new positions
        new_position = [last_position[0] + delta_x,
                        last_position[1] + delta_y,
                        last_position[2] + delta_z]

        print(f"Timestamp: {timestamp}")
        print(f"True East Velocity: {true_east_velocity} m/s")
        print(f"True North Velocity: {true_north_velocity} m/s")
        print(f"Up Velocity: {up_velocity} m/s")
        print(f"Delta X: {delta_x} m")
        print(f"Delta Y: {delta_y} m")
        print(f"Delta Z: {delta_z} m")
        print(f"New Position: {new_position}\n")

        # adding new data to dataframe
        global df
        df.loc[len(df)] = [timestamp, true_east_velocity, true_north_velocity, up_velocity,
                           new_position[0], new_position[1], new_position[2]]
        
        # update of last positions
        last_position = new_position
        
    except ValueError as e:
        print(f"Error parsing PGRMV data: {e}")

if __name__ == "__main__":
    read_gps_data()

