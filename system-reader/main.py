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

import asyncio
import datetime
import random
import websockets


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
            print("----- SUB Hardware -----")
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


# WS server that sends messages at random intervals


async def time(websocket, path):
    while True:
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
        try:
            await websocket.send(serialized_data)
        except websockets.exceptions.ConnectionClosed:
            # websocket.close()
            cprint(COLORS.YELLOW, "Client disconnected")
            break
        await asyncio.sleep(1)

if __name__ == "__main__":
    # LibreHardwareHandle = initialize_librehardwaremonitor()
    # fetch_stats(LibreHardwareHandle)

    start_server = websockets.serve(time, "127.0.0.1", 2346)
    cprint(COLORS.CYAN, "Listening on port 2346")

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
