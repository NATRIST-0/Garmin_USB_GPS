
"""
Garmin_Scrolling_Plot_CSV_Color
"""

import serial, pynmea2, geopy.distance, csv, datetime, matplotlib.pyplot as plt

start_point = (0, 0)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
cmap = plt.cm.RdYlGn

x_coords = []
y_coords = []
z_coords = []

max_num_satellites = 12 

sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=8, vmax=max_num_satellites))
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, pad=0.1)
cbar.set_label('Number of Satellites Connected')

def main():
    serial_port = 'COM8'
    baud_rate = 4800

    ser = serial.Serial(serial_port, baud_rate)

    with open('garmin_gps_data_.csv', 'w', newline='') as csvfile:
        fieldnames = ['Timestamp', 'Latitude', 'Longitude', 'Altitude', 'Length (m)', 'Width (m)', 'Num Satellites']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        start_time = datetime.datetime.now()

        try:
            while True:
                data = ser.readline().decode('latin-1')

                if data.startswith('$'):
                    try:
                        msg = pynmea2.parse(data)
                        if isinstance(msg, pynmea2.GGA):
                            global start_point 
                            global max_num_satellites
                            num_satellites = int(msg.num_sats) 
                            if start_point == (0, 0):  
                                start_point = (msg.latitude, msg.longitude)
                            x = geopy.distance.geodesic(start_point, (msg.latitude, start_point[1])).meters
                            y = geopy.distance.geodesic(start_point, (start_point[0], msg.longitude)).meters

                            x_coords.append(x)
                            y_coords.append(y)
                            z_coords.append(msg.altitude)

                            elapsed_time = (datetime.datetime.now() - start_time).total_seconds() / 60.0

                            writer.writerow({'Timestamp': elapsed_time,
                                             'Latitude': msg.latitude,
                                             'Longitude': msg.longitude,
                                             'Altitude': msg.altitude,
                                             'Length (m)': x,
                                             'Width (m)': y, 
                                             'Num Satellites': num_satellites}) 
                            ax.clear()
                            color=cmap(num_satellites / max_num_satellites)
                            ax.plot(x_coords, y_coords, z_coords, color=color)
                            ax.set_xlabel('Length (m)')
                            ax.set_ylabel('Width (m)')
                            ax.set_zlabel('Altitude (m)')

                            sm.set_clim(vmin=8, vmax=max_num_satellites)

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