#!/usr/bin/env python3
# author: Tristan Gayrard

"""
Garmin_Read_PGRMV_sentence_CSV
"""

import csv
import serial
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

ser = serial.Serial(
    port='COM9', 
    baudrate=4800,        
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

# making empty dataframes to store all values
df = pd.DataFrame(columns=['Timestamp', 'time (s)','True East Velocity (m/s)', 'True North Velocity (m/s)', 'Up Velocity (m/s)', 
                           'X (m)', 'Y (m)', 'Z (m)'])

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

def read_gps_data():
    last_timestamp = None
    last_position = [0, 0, 0]  # initial position

    # Open the CSV file once and write the header
    with open('garmin_gps_data.csv', 'w', newline='') as csvfile:
        fieldnames = ['Timestamp', 'time (s)', 'True East Velocity (m/s)', 'True North Velocity (m/s)', 
                      'Up Velocity (m/s)', 'X (m)', 'Y (m)', 'Z (m)']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
    
    while True:
        try:
            line = ser.readline().decode('ascii', errors='replace').strip()
            if line:
                if line.startswith('$PGRMV'):
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    last_timestamp, last_position = parse_pgrmv(line, timestamp, last_timestamp, last_position)
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
        return last_timestamp, last_position

    try:
        true_east_velocity = float(parts[1])
        true_north_velocity = float(parts[2])
        up_velocity = float(parts[3].split('*')[0])

        # calculation of position in function of speed
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
        print(f"\u0394 t {delta_t}")
        print(f"True East Velocity: {true_east_velocity} m/s")
        print(f"True North Velocity: {true_north_velocity} m/s")
        print(f"Up Velocity: {up_velocity} m/s")
        print(f"\u0394 X: {delta_x} m")
        print(f"\u0394 Y: {delta_y} m")
        print(f"\u0394 Z: {delta_z} m")
        print(f"New Position: {new_position}\n")

        # adding new data to dataframe
        global df
        df.loc[len(df)] = [timestamp, delta_t, true_east_velocity, true_north_velocity, up_velocity,
                           new_position[0], new_position[1], new_position[2]]
        
        # clear the axis and plot the new data
        ax.clear()
        ax.plot(df['X (m)'], df['Y (m)'], df['Z (m)'], color='steelblue')
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_zlabel('Z (m)')
        plt.title('Tracking Position of GPS')
        plt.draw()
        plt.pause(0.05)
        
        # Append new data to the CSV file
        with open('garmin_gps_data_.csv', 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=df.columns)
            writer.writerow({'Timestamp': timestamp,
                             'time (s)': delta_t,
                             'True East Velocity (m/s)': true_east_velocity,
                             'True North Velocity (m/s)': true_north_velocity,
                             'Up Velocity (m/s)': up_velocity,
                             'X (m)': new_position[0], 
                             'Y (m)': new_position[1],
                             'Z (m)': new_position[2]}) 
    
        return timestamp, new_position
        
    except ValueError as e:
        print(f"Error parsing PGRMV data: {e}")
        return last_timestamp, last_position

if __name__ == "__main__":
    read_gps_data()
