
"""
Garmin_Scrolling_Plot_CSV
"""

import serial
import pynmea2
import matplotlib.pyplot as plt
import geopy.distance
import csv
import datetime

start_point = (0, 0)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

x_coords = []
y_coords = []
z_coords = []

num_satellites = 0

def main():
    serial_port = 'COM8'
    baud_rate = 4800

    ser = serial.Serial(serial_port, baud_rate)

    with open('garmin_gps_data_.csv', 'w', newline='') as csvfile:
        fieldnames = ['Timestamp', 'Latitude', 'Longitude', 'Altitude', 'Lenght (m)', 'Width (m)', 'Num Satellites']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        start_time = datetime.datetime.now()

        try:
            while True:
                data = ser.readline().decode('utf-8')

                if data.startswith('$'):
                    try:
                        msg = pynmea2.parse(data)
                        if isinstance(msg, pynmea2.GGA):
                            global start_point, num_satellites  
                            num_satellites = msg.num_sats  

                            if start_point == (0, 0):  
                                start_point = (msg.latitude, msg.longitude)
                            x = geopy.distance.geodesic(start_point, (msg.latitude, start_point[1])).meters
                            y = geopy.distance.geodesic(start_point, (start_point[0], msg.longitude)).meters

                  
                            x_coords.append(x)
                            y_coords.append(y)
                            z_coords.append(msg.altitude)
                            
                            print(f"x = {x:.5f} m,\ny = {y:.5f} m,\nz = {msg.altitude:.5f} m\nNombre de satellites connectés : {num_satellites}")


                            elapsed_time = (datetime.datetime.now() - start_time).total_seconds() / 60.0

                            writer.writerow({'Timestamp': elapsed_time,
                                             'Latitude': msg.latitude,
                                             'Longitude': msg.longitude,
                                             'Altitude': msg.altitude,
                                             'Lenght (m)': x,
                                             'Width (m)': y,  
                                             'Num Satellites': num_satellites}) 

                            ax.clear()
                            ax.plot(x_coords, y_coords, z_coords)
                            ax.set_xlabel('Lenght (m)')
                            ax.set_ylabel('Width (m)')
                            ax.set_zlabel('Altitude (m)')

                            plt.title('Path of GPS')
                            plt.draw()
                            plt.pause(0.05)

                        elif isinstance(msg, pynmea2.RMC):
                            print(f"\nSpeed = {msg.spd_over_grnd} m/s")
                    except pynmea2.ParseError as e:
                        print("Error when analyzing the NMEA:", e)


        except KeyboardInterrupt:
            ser.close()

if __name__ == "__main__":
    main()
