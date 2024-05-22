# -*- coding: utf-8 -*-
"""
Garmin_Activate_PGRMV_sentence, plus reading of the incoming data
"""

import serial


ser = serial.Serial(
    port='COM9', 
    baudrate=4800,        
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

def send_command(command):
    ser.write(f"{command}\r\n".encode('ascii'))
    print(f"Command sent: {command}")

def read_gps_data():
    while True:
        try:
            line = ser.readline().decode('ascii', errors='replace').strip()
            if line:
                if line.startswith('$PGRMV'):
                    parse_pgrmv(line)
        except serial.SerialException as e:
            print(f"Serial error: {e}")
        except KeyboardInterrupt:
            print("Exiting...")
            break

def parse_pgrmv(data):
    # $PGRMV,<True east velocity>,<True north velocity>,<Up velocity>*hh
    parts = data.split(',')
    if len(parts) < 4:
        print("Invalid PGRMV data")
        return

    try:
        true_east_velocity = float(parts[1])
        true_north_velocity = float(parts[2])
        up_velocity = float(parts[3].split('*')[0])  # Extraire la valeur avant le checksum

        print(f"True East Velocity: {true_east_velocity} m/s")
        print(f"True North Velocity: {true_north_velocity} m/s")
        print(f"Up Velocity: {up_velocity} m/s")
    except ValueError as e:
        print(f"Error parsing PGRMV data: {e}")

if __name__ == "__main__":
    send_command("$PGRMO,PGRMV,1")  # 1 pour activer, 0 pour désactiver
    read_gps_data()
