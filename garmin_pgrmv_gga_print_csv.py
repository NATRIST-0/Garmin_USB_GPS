# -*- coding: utf-8 -*-
"""
Created on Tue May 28 13:57:38 2024

@author: GAYRARD
"""

import csv
import serial
import pynmea2
import geopy.distance
from datetime import datetime

# Initialize variables
start_point = None
x_coords = []
y_coords = []
z_coords = []
num_satellites = 0
last_timestamp = None
last_position = [0, 0, 0]  # initial position
start_time = datetime.now()  # Initialize start time here

def write_to_csv(csv_writer, row_data):
    csv_writer.writerow(row_data)

def parse_pgrmv(data, timestamp1, last_timestamp, last_position):
    parts = data.split(',')
    if len(parts) < 4:
        print("Invalid PGRMV data")
        return last_timestamp, last_position, {}

    try:
        true_east_velocity = float(parts[1])
        true_north_velocity = float(parts[2])
        up_velocity = float(parts[3].split('*')[0])

        delta_t = 0
        if last_timestamp:
            delta_t = (datetime.strptime(timestamp1, '%Y-%m-%d %H:%M:%S') - 
                       datetime.strptime(last_timestamp, '%Y-%m-%d %H:%M:%S')).total_seconds()

        delta_x = true_east_velocity * delta_t
        delta_y = true_north_velocity * delta_t
        delta_z = up_velocity * delta_t

        new_position = [last_position[0] + delta_x,
                        last_position[1] + delta_y,
                        last_position[2] + delta_z]

        print(f"Timestamp1: {timestamp1}")
        print(f"Δ t {delta_t}")
        print(f"True East Velocity: {true_east_velocity} m/s")
        print(f"True North Velocity: {true_north_velocity} m/s")
        print(f"Up Velocity: {up_velocity} m/s")
        print(f"Δ X: {delta_x} m")
        print(f"Δ Y: {delta_y} m")
        print(f"Δ Z: {delta_z} m")
        print(f"New Position: {new_position}\n")

        pgrmv_data = {
            'Timestamp1': timestamp1,
            'time (s)': delta_t,
            'True East Velocity (m/s)': true_east_velocity,
            'True North Velocity (m/s)': true_north_velocity,
            'Up Velocity (m/s)': up_velocity,
            'X1 (m)': new_position[0], 
            'Y1 (m)': new_position[1],
            'Z1 (m)': new_position[2]
        }

        return timestamp1, new_position, pgrmv_data

    except ValueError as e:
        print(f"Error parsing PGRMV data: {e}")
        return last_timestamp, last_position, {}

def main():
    global start_point, last_timestamp, last_position, start_time

    ser = serial.Serial(port='COM9', baudrate=9600, parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1)

    with open('garmin_gps_data.csv', 'w', newline='') as csvfile:
        fieldnames = ['Timestamp1', 'time (s)', 'True East Velocity (m/s)', 'True North Velocity (m/s)', 'Up Velocity (m/s)', 
                      'X1 (m)', 'Y1 (m)', 'Z1 (m)', 'Timestamp2', 'Latitude', 'Longitude', 'Altitude', 'X2 (m)', 'Y2 (m)', 'Z2 (m)']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        row_data = {}  # Initialize an empty dictionary to store the row data

        try:
            while True:
                data = ser.readline().decode('utf-8')

                if data.startswith('$'):
                    try:
                        msg = pynmea2.parse(data)
                        if isinstance(msg, pynmea2.GGA):
                            if start_point is None:  
                                start_point = (msg.latitude, msg.longitude)
                                start_alt = msg.altitude

                            x = geopy.distance.geodesic(start_point, (msg.latitude, start_point[1])).meters
                            y = geopy.distance.geodesic(start_point, (start_point[0], msg.longitude)).meters
                            z = start_alt - msg.altitude

                            x_coords.append(x)
                            y_coords.append(y)
                            z_coords.append(z)

                            elapsed_time = (datetime.now() - start_time).total_seconds() / 60.0

                            row_data.update({
                                'Timestamp2': elapsed_time,
                                'Latitude': msg.latitude,
                                'Longitude': msg.longitude,
                                'Altitude': msg.altitude,
                                'X2 (m)': x,
                                'Y2 (m)': y,
                                'Z2 (m)': z
                            })
                                               
                            print('elapsed_time', elapsed_time)
                            print('msg.latitude', msg.latitude)
                            print('msg.longitude', msg.longitude)
                            print('msg.altitude', msg.altitude)
                            print('x', x)
                            print('y', y)
                            print('z', z)
                            print('\n')

                            # If PGRMV data was also parsed, write the combined data to CSV
                            if 'Timestamp1' in row_data:
                                write_to_csv(writer, row_data)
                                row_data = {}  # Clear row_data for the next set

                        elif data.startswith('$PGRMV'):
                            timestamp1 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            last_timestamp, last_position, pgrmv_data = parse_pgrmv(data, timestamp1, last_timestamp, last_position)
                            row_data.update(pgrmv_data)

                            # If GGA data was also parsed, write the combined data to CSV
                            if 'Timestamp2' in row_data:
                                write_to_csv(writer, row_data)
                                row_data = {}  # Clear row_data for the next set
                        
                    except pynmea2.ParseError as e:
                        print("Error when analyzing the NMEA:", e)

        except KeyboardInterrupt:
            print("Exiting...")
            ser.close()
            print("Serial port closed")

if __name__ == "__main__":
    main()
