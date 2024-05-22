
"""
GPS_Garmin_Read
"""

import serial  
import pynmea2 

def main():
    serial_port = 'COM8'  
    baud_rate = 4800  

    ser = serial.Serial(serial_port, baud_rate)

    try:
        while True:
            data = ser.readline().decode('utf-8')

            if data.startswith('$'):
                try:
                    msg = pynmea2.parse(data)  
                    if isinstance(msg, pynmea2.GGA):
                        print("Latitude:", msg.latitude)
                        print("Longitude:", msg.longitude)
                        print("Altitude:", msg.altitude)
                    elif isinstance(msg, pynmea2.RMC): 
                        print("\nVitesse:", msg.spd_over_grnd)
                except pynmea2.ParseError as e:
                    print("Erreur lors de l'analyse de la trame NMEA:", e)

    except KeyboardInterrupt:
        ser.close()

if __name__ == "__main__":
    main()
