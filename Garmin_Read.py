"""
Garmin_Read_PGRMV_sentence_CSV
"""

import csv
import serial
import pynmea2
import pandas as pd
import geopy.distance
from datetime import datetime
import matplotlib.pyplot as plt

def main():
    csv_filename = input(str("Name of the csv file data will be stored in :"))
    port = input("USB port used: ")

    ser = serial.Serial(
        port=port,
        baudrate=4800,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1
    )

    # Initialize data structures
    data = []

    # Set up plotting
    plt.ion()
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    start_point = None
    x_coords = []
    y_coords = []

    # Initialize CSV file with headers
    fieldnames = ['Timestamp1', 'time (s)', 'True East Velocity (m/s)', 'True North Velocity (m/s)', 'Up Velocity (m/s)', 
                  'X', 'Y', 'Z', 'Timestamp2', 'Latitude', 'Longitude', 'Altitude', 'Length (m)', 'Width (m)']

    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    try:
        while True:
            line = ser.readline().decode('ascii', errors='replace').strip()
            if line:
                if line.startswith('$PGRMV'):
                    timestamp1 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    data_entry = parse_pgrmv(line, timestamp1, data)
                    if data_entry:
                        data.append(data_entry)
                        update_plot(ax, data)
                        save_to_csv(csv_filename, data_entry, fieldnames)

                elif line.startswith('$GPGGA'):
                    timestamp2 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    data_entry = parse_gpgga(line, timestamp2, data, start_point, x_coords, y_coords)
                    if start_point is None and data_entry:
                        start_point = (data_entry['Latitude'], data_entry['Longitude'])
                    if data_entry and data:
                        data[-1].update(data_entry)
                        update_plot(ax, data)
                        save_to_csv(csv_filename, data[-1], fieldnames)

    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        ser.close()
        print("Serial port closed")

def parse_pgrmv(data, timestamp1, previous_data):
    parts = data.split(',')
    if len(parts) < 4:
        print("Invalid PGRMV data")
        return None

    try:
        true_east_velocity = float(parts[1])
        true_north_velocity = float(parts[2])
        up_velocity = float(parts[3].split('*')[0])

        last_position = previous_data[-1] if previous_data else {'X': 0, 'Y': 0, 'Z': 0, 'Timestamp1': timestamp1}
        delta_t = (datetime.strptime(timestamp1, '%Y-%m-%d %H:%M:%S') - 
                   datetime.strptime(last_position['Timestamp1'], '%Y-%m-%d %H:%M:%S')).total_seconds()

        delta_x = true_east_velocity * delta_t
        delta_y = true_north_velocity * delta_t
        delta_z = up_velocity * delta_t

        new_position = {
            'Timestamp1': timestamp1,
            'time (s)': delta_t,
            'True East Velocity (m/s)': true_east_velocity,
            'True North Velocity (m/s)': true_north_velocity,
            'Up Velocity (m/s)': up_velocity,
            'X': last_position['X'] + delta_x,
            'Y': last_position['Y'] + delta_y,
            'Z': last_position['Z'] + delta_z,
            'Timestamp2': None,
            'Latitude': None,
            'Longitude': None,
            'Altitude': None,
            'Length (m)': None,
            'Width (m)': None
        }
        return new_position

    except ValueError as e:
        print(f"Error parsing PGRMV data: {e}")
        return None

def parse_gpgga(data, timestamp2, previous_data, start_point, x_coords, y_coords):
    try:
        msg = pynmea2.parse(data)
        if isinstance(msg, pynmea2.GGA):
            latitude = msg.latitude
            longitude = msg.longitude
            altitude = msg.altitude

            if start_point:
                x = geopy.distance.geodesic(start_point, (latitude, start_point[1])).meters
                y = geopy.distance.geodesic(start_point, (start_point[0], longitude)).meters
                x_coords.append(x)
                y_coords.append(y)
            else:
                x = y = 0

            data_entry = {
                'Timestamp2': timestamp2,
                'Latitude': latitude,
                'Longitude': longitude,
                'Altitude': altitude,
                'Length (m)': x,
                'Width (m)': y
            }

            return data_entry

    except ValueError as e:
        print(f"Error parsing GPGGA data: {e}")
        return None

def update_plot(ax, data):
    df = pd.DataFrame(data)
    ax.clear()
    ax.plot(df['X'], df['Y'], df['Z'], color='steelblue')
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')
    plt.title('Tracking Position of GPS')
    plt.draw()
    plt.pause(0.05)

def save_to_csv(filename, data_entry, fieldnames):
    with open(filename, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow(data_entry)

if __name__ == "__main__":
    main()