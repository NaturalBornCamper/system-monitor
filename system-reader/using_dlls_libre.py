"""
This uses StackOverflow answer: https://stackoverflow.com/a/49909330/1046013
Same as pytherm.py, however it also uses CPUThermometer, which is a sort of fork of OpenHardwareMonitor
However, CPU Thermometer's dll seems to be 32bits (Even if website says both are included), so it won't load on
Python 64 bits. It's not needed anyways as it doesn't give any additional info after OpenHardwareMonitor
"""

import clr  # package pythonnet, not clr
import os

hardware_types = [
    "Motherboard",
    "SuperIO",
    "Cpu",
    "Memory",
    "GpuNvidia",
    "GpuAmd",
    "Storage",
    "Network",
    "Cooler",
]

sensor_types = [
    "Voltage",  # V
    "Clock",  # MHz
    "Temperature",  # Celcius
    "Load",  # %
    "Frequency",  # Hz
    "Fan",  # RPM
    "Flow",  # L/h
    "Control",  # %
    "Level",  # %
    "Factor",  # 1
    "Power",  # W
    "Data",  # GB = 2^30 Bytes
    "SmallData",  # MB = 2^20 Bytes
    "Throughput",  # B/s
]

sensor_units = [
    "V",
    "MHz",
    "\u00B0C",
    "%",
    "Hz",
    "RPM",
    "L/h",
    "%",
    "%",
    "1",
    "W",
    "GB = 2^30 Bytes",
    "MB = 2^20 Bytes",
    "B/s",
]


def initialize_librehardwaremonitor():
    file = 'lib/LibreHardwareMonitorLib.dll'
    # clr.AddReference(file)
    clr.AddReference(os.path.abspath(os.path.dirname(__file__)) + R'\lib/LibreHardwareMonitorLib.dll')
    # clr.AddReference(os.path.abspath(os.path.dirname(__file__)) + R'\lib/HidSharp.dll')

    from LibreHardwareMonitor import Hardware
    import inspect

    handle = Hardware.Computer()
    # handle = Hardware.Computer(True) # Doesn't work
    # handle = Hardware.Computer(IsCpuEnabled=True) # Doesn't work
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
            hardware_types[sensor.Hardware.HardwareType],
            sensor.Hardware.Name,
            sensor_types[sensor.SensorType],
            sensor.Index,
            sensor.Name,
            sensor.Value,
            sensor_units[sensor.SensorType],
        ))
        # if sensor.SensorType == sensor_types.index('Temperature'):
        #     print(u"%s %s Temperature Sensor #%i %s - %s\u00B0C" % (
        #         hardware_types[sensor.Hardware.HardwareType], sensor.Hardware.Name, sensor.Index, sensor.Name,
        #         sensor.Value))


# Look at sensor class for attributes
# search "13" "11" etc etc to find sensor types

if __name__ == "__main__":
    print("LibreHardwareMonitor:")
    LibreHardwareHandle = initialize_librehardwaremonitor()
    fetch_stats(LibreHardwareHandle)
