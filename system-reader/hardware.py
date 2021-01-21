# noinspection PyPackageRequirements
import clr  # From package "pythonnet", not package "clr"
# from pythonnet import clr  # Not working, got to use line above
import os
import sys
import glob
from pyrotools.console import cprint, COLORS

from constants import HARDWARE_TYPES, SENSORS


def initialize_librehardwaremonitor():
    file = 'lib/LibreHardwareMonitorLib.dll'
    # clr.AddReference(file)
    clr.AddReference(os.path.abspath(os.path.dirname(__file__)) + R'\lib/LibreHardwareMonitorLib.dll')
    # clr.AddReference(os.path.abspath(os.path.dirname(__file__)) + R'\lib/HidSharp.dll')

    # noinspection PyUnresolvedReferences
    from LibreHardwareMonitor import Hardware

    handle = Hardware.Computer()
    handle.IsCpuEnabled = True
    handle.IsGpuEnabled = True
    handle.IsMemoryEnabled = True
    handle.IsMotherboardEnabled = True
    handle.IsControllerEnabled = True
    handle.IsNetworkEnabled = True
    handle.IsStorageEnabled = True

    # from pprint import pprint
    # pprint([i for i in Hardware.Computer.__dict__.keys() if i[:1] != '_'])

    # for att in dir(handle):
    #     print(att, getattr(handle, att))

    handle.Open()
    return handle


# CHECk IF MAIN COMPUTER HAS SUB HARDWARE
# CHECk IF MAIN COMPUTER HAS SUB HARDWARE
# CHECk IF MAIN COMPUTER HAS SUB HARDWARE
# CHECk IF MAIN COMPUTER HAS SUB HARDWARE
# CHECk IF MAIN COMPUTER HAS SUB HARDWARE
# CHECK C# IF SENSORS HAVE SOME SORT OF UPDATE FUNCTION SO THAT HARDWARE CALLS UPDATE() ONLY ONCE THEN SENSORS INDIVIDUALLY UPDATE
# CHECK C# IF SENSORS HAVE SOME SORT OF UPDATE FUNCTION SO THAT HARDWARE CALLS UPDATE() ONLY ONCE THEN SENSORS INDIVIDUALLY UPDATE
# CHECK C# IF SENSORS HAVE SOME SORT OF UPDATE FUNCTION SO THAT HARDWARE CALLS UPDATE() ONLY ONCE THEN SENSORS INDIVIDUALLY UPDATE
# CHECK C# IF SENSORS HAVE SOME SORT OF UPDATE FUNCTION SO THAT HARDWARE CALLS UPDATE() ONLY ONCE THEN SENSORS INDIVIDUALLY UPDATE
# CHECK C# IF SENSORS HAVE SOME SORT OF UPDATE FUNCTION SO THAT HARDWARE CALLS UPDATE() ONLY ONCE THEN SENSORS INDIVIDUALLY UPDATE
# CHECK C# IF SENSORS HAVE SOME SORT OF UPDATE FUNCTION SO THAT HARDWARE CALLS UPDATE() ONLY ONCE THEN SENSORS INDIVIDUALLY UPDATE

def fetch_stats(handle):
    # from pprint import pprint
    # pprint(handle.Hardware)
    for h, hardware in enumerate(handle.Hardware):
        hardware.Update()
        cprint(COLORS.BRIGHT_BLUE, "HARDWARE TYPE: {}, NAME: {} ({}, {})".format(
            HARDWARE_TYPES[hardware.HardwareType],
            hardware.Name,
            f"{len(hardware.Sensors)} sensor(s)",
            f"{len(hardware.SubHardware)} sub hardware(s)"
        ))

        if len(hardware.Sensors):
            cprint(COLORS.BRIGHT_MAGENTA, "Sensors:")
            for s, sensor in enumerate(hardware.Sensors):
                # for att in dir(sensor):
                #     print(att, getattr(sensor, att))
                parse_sensor(sensor, hardware_index=h, sensor_index=s)

        if len(hardware.SubHardware):
            cprint(COLORS.RED, "SubHardware:")
            for sh, sub_hardware in enumerate(hardware.SubHardware):
                sub_hardware.Update()
                cprint(COLORS.BRIGHT_MAGENTA, "Sensors:")
                for s, sensor in enumerate(sub_hardware.Sensors):
                    parse_sensor(sensor, hardware_index=h, sub_hardware_index=sh, sensor_index=s)
        print("")


def parse_sensor(sensor, hardware_index=None, sub_hardware_index=None, sensor_index=None):
    # print(sensor.Value)
    if sensor.Value is not None:
        # print(sensor.SensorType)
        # print("HW type:{}, HW name:{}, Sensor type: {}, Sensor id: {}, Sensor name:{}, Sensor value: {} {}".format(
        #     HARDWARE_TYPES[sensor.Hardware.HardwareType],
        #     sensor.Hardware.Name,
        #     SENSORS[sensor.SensorType].name,
        #     sensor.Index,
        #     sensor.Name,
        #     sensor.Value,
        #     SENSORS[sensor.SensorType].unit,
        # ))

        cprint(COLORS.GREEN, "Type: {}, Id: {}, Name: {}, Value: {} {}, Indexes [Hardware, Sub-Hardware, Sensor]: [{}, {}, {}]".format(
            SENSORS[sensor.SensorType].name,
            sensor.Index,
            sensor.Name,
            sensor.Value,
            SENSORS[sensor.SensorType].unit,
            hardware_index,
            sub_hardware_index,
            sensor_index,
        ))
