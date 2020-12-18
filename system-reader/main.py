"""
This uses StackOverflow answer: https://stackoverflow.com/a/49909330/1046013
Same as using_openhardwaremonitor1.py, however it also uses CPUThermometer, which is a sort of fork of OpenHardwareMonitor
However, CPU Thermometer's dll seems to be 32bits (Even if website says both are included), so it won't load on
Python 64 bits. It's not needed anyways as it doesn't give any additional info after OpenHardwareMonitor
"""
import json
from pprint import pprint

from pyrotools.console import cprint, COLORS

from constants import SERIAL_PORT, ERROR_SERIAL, HARDWARE_TYPES, SENSORS, SERIAL_BAUD_RATE, SERIAL_RTSCTS

# noinspection PyPackageRequirements
import clr  # From package "pythonnet", not package "clr"
# from pythonnet import clr  # Not working, got to use line above
import os
import sys
import glob
import serial


def get_serial_ports():
    """ Lists serial serial_port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def initialize_librehardwaremonitor():
    file = 'lib/LibreHardwareMonitorLib.dll'
    # clr.AddReference(file)
    clr.AddReference(os.path.abspath(os.path.dirname(__file__)) + R'\lib/LibreHardwareMonitorLib.dll')
    # clr.AddReference(os.path.abspath(os.path.dirname(__file__)) + R'\lib/HidSharp.dll')

    # noinspection PyUnresolvedReferences
    from LibreHardwareMonitor import Hardware

    handle = Hardware.Computer()
    # handle = Hardware.Computer(True) # Doesn't work
    # handle = Hardware.Computer(IsCpuEnabled=True)  # Doesn't work
    # handle = Hardware.Computer({"IsCpuEnabled": True})  # Doesn't work
    handle.IsCpuEnabled = True
    handle.IsGpuEnabled = True
    handle.IsMemoryEnabled = True
    handle.IsMotherboardEnabled = True
    handle.IsControllerEnabled = True
    handle.IsNetworkEnabled = True
    handle.IsStorageEnabled = True
    # print(handle.IsCpuEnabled)
    # print(handle.IsGpuEnabled)
    # print(handle.IsMemoryEnabled)
    # print(handle.IsMotherboardEnabled)
    # print(handle.IsControllerEnabled)
    # print(handle.IsNetworkEnabled)
    # print(handle.IsStorageEnabled)

    # from pprint import pprint
    # pprint([i for i in Hardware.Computer.__dict__.keys() if i[:1] != '_'])

    # for att in dir(handle):
    #     print(att, getattr(handle, att))

    handle.Open()
    return handle


def fetch_stats(handle):
    # from pprint import pprint
    # pprint(handle.Hardware)
    for i in handle.Hardware:
        i.Update()
        print(i.Name)
        for sensor in i.Sensors:
            # for att in dir(sensor):
            #     print(att, getattr(sensor, att))
            parse_sensor(sensor)
        for j in i.SubHardware:
            j.Update()
            for subsensor in j.Sensors:
                parse_sensor(subsensor)


def parse_sensor(sensor):
    # print(sensor.Value)
    if sensor.Value is not None:
        # print(sensor.SensorType)
        print("{} - {}, {} Sensor {}: {} - {} {}".format(
            HARDWARE_TYPES[sensor.Hardware.HardwareType],
            sensor.Hardware.Name,
            SENSORS[sensor.SensorType].name,
            sensor.Index,
            sensor.Name,
            sensor.Value,
            SENSORS[sensor.SensorType].unit,
        ))


if __name__ == "__main__":
    available_serial_ports = get_serial_ports()
    pprint(available_serial_ports)
    if SERIAL_PORT in available_serial_ports:
        serial_port = SERIAL_PORT
        cprint(COLORS.GREEN, "Opened serial serial_port {}".format(serial_port))
    elif available_serial_ports:
        serial_port = available_serial_ports[0]
        cprint(COLORS.YELLOW, "Port {} is unavailable, connecting to available serial_port {} instead".format(
            SERIAL_PORT,
            serial_port
        ))
    else:
        cprint(COLORS.RED, "No serial serial_port available, including requested serial_port {}".format(SERIAL_PORT))
        sys.exit(ERROR_SERIAL)

    ser = serial.Serial(
        port=serial_port,
        baudrate=SERIAL_BAUD_RATE,
        parity=serial.PARITY_EVEN,
        rtscts=SERIAL_RTSCTS
    )

    # LibreHardwareHandle = initialize_librehardwaremonitor()
    # fetch_stats(LibreHardwareHandle)

    # Don't know which to use
    data = {
        "cpu": {
            "temperature": 40,
            "usage": "50%"
        },
        "memory": {
            "temperature": 50,
            "usage": "20%"
        },
    }
    serialized_data = json.dumps(data)
    cprint(COLORS.CYAN, serialized_data)
    serialized_encoded_data = serialized_data.encode(encoding='utf-8')
    cprint(COLORS.CYAN, serialized_encoded_data)
    res_dict = json.loads(serialized_encoded_data.decode(encoding='utf-8'))
    ser.write(serialized_encoded_data)
    # ser.write(serialized_encoded_data + b'\n')  # Better for use with readline()?
    # ser.writelines(serialized_encoded_data + b'\n')  # Better for use with readLine()?
    # ser.write(b"Hello")
    # ser.write("Hello".encode())
    # ser.write("Hello".encode(encoding="ascii")) # Can't encode special characters however

    ser.close()
