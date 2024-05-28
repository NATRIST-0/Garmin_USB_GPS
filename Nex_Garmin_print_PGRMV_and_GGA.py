#!/usr/bin/env python3
# author: Tristan Gayrard

"""
Garmin_Read_PGRMV_and_GGA_CSV
"""

import csv
import serial
import pandas as pd
import pynmea2
import geopy.distance
from datetime import datetime

# Initialize variables
start_point = None
x_coords = []
y_coords = []
z_coords = []
num_satellites = 0

def parse_pgrmv(data, timestamp1, last_timestamp, last_position, df):
    parts = data.split(',')
    if len(parts) < 4:
        print("Invalid PGRMV data")
        return last_timestamp, last_position

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
        print(f"\u0394 t {delta_t}")
        print(f"True East Velocity: {true_east_velocity} m/s")
        print(f"True North Velocity: {true_north_velocity} m/s")
        print(f"Up Velocity: {up_velocity} m/s")
        print(f"\u0394 X: {delta_x} m")
        print(f"\u0394 Y: {delta_y} m")
        print(f"\u0394 Z: {delta_z} m")
        print(f"New Position: {new_position}\n")

        row_data = {
            'Timestamp1': timestamp1,
            'time (s)': delta_t,
            'True East Velocity (m/s)': true_east_velocity,
            'True North Velocity (m/s)': true_north_velocity,
            'Up Velocity (m/s)': up_velocity,
            'X (m)': new_position[0], 
            'Y (m)': new_position[1],
            'Z (m)': new_position[2]
        }

        # Adding a row to the DataFrame
        df.loc[-1] = row_data
        df.index = df.index + 1  # Shifting index
        df = df.sort_index()  # Sorting by index
        
        # Write row to CSV file
        with open('garmin_gps_data_.csv', 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=row_data.keys())
            writer.writerow(row_data)
        
        return timestamp1, new_position
        
    except ValueError as e:
        print(f"Error parsing PGRMV data: {e}")
        return last_timestamp, last_position


def main():
    global start_point
    # csv_filename = str(input("Name of the csv file data will be stored in :"))
    # port = input("USB port used: ")
    # baudrate = int(input("Baud Rate = "))
    ser = serial.Serial(port='COM9', baudrate=9600, parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1)

    df = pd.DataFrame(columns=['Timestamp1', 'time (s)', 'True East Velocity (m/s)', 'True North Velocity (m/s)', 'Up Velocity (m/s)', 
                  'X', 'Y', 'Z', 'Timestamp2', 'Latitude', 'Longitude', 'Altitude', 'Length (m)', 'Width (m)'])

    last_timestamp = None
    last_position = [0, 0, 0]  # initial position

    with open('test', 'w', newline='') as csvfile:
        fieldnames = ['Timestamp1', 'time (s)', 'True East Velocity (m/s)', 'True North Velocity (m/s)', 'Up Velocity (m/s)', 
                      'X', 'Y', 'Z', 'Timestamp2', 'Latitude', 'Longitude', 'Altitude', 'Length (m)', 'Width (m)']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        start_time = datetime.now()

        try:
            while True:
                data = ser.readline().decode('utf-8')

                if data.startswith('$'):
                    try:
                        msg = pynmea2.parse(data)
                        if isinstance(msg, pynmea2.GGA):
 
                            if start_point == None:  
                                start_point = (msg.latitude, msg.longitude)
                            x = geopy.distance.geodesic(start_point, (msg.latitude, start_point[1])).meters
                            y= geopy.distance.geodesic(start_point, (start_point[0], msg.longitude)).meters

                            x_coords.append(x)
                            y_coords.append(y)
                            z_coords.append(msg.altitude)

                            elapsed_time = (datetime.now() - start_time).total_seconds() / 60.0

                            writer.writerow({'Timestamp2': elapsed_time,
                                             'Latitude': msg.latitude,
                                             'Longitude': msg.longitude,
                                             'Altitude': msg.altitude,
                                             'Length (m)': x,
                                             'Width (m)': y 
                                              }) 
                            print('elapsed_time', elapsed_time)
                            print('msg.latitude', msg.latitude)
                            print('msg.longitude', msg.longitude)
                            print('msg.altitude', msg.altitude)
                            print('x', x)
                            print('y', y)
                            print('\n')
                            

                        elif data.startswith('$PGRMV'):
                            timestamp1 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            last_timestamp, last_position = parse_pgrmv(data, timestamp1, last_timestamp, last_position, df)
                        
                    except pynmea2.ParseError as e:
                        print("Error when analyzing the NMEA:", e)

        except KeyboardInterrupt:
            print("Exiting...")
            ser.close()
            print("Serial port closed")

if __name__ == "__main__":
    main()
