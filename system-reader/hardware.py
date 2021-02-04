# noinspection PyPackageRequirements
import clr  # From package "pythonnet", not package "clr"
# from pythonnet import clr  # Not working, got to use line above
import os
import sys
import asyncio
import glob
import time
from pyrotools.console import cprint, COLORS
from collections import defaultdict

from constants import HARDWARE_TYPES, SENSORS, INDEX_HARDWARE, INDEX_SENSOR, INDEX_SUB_HARDWARE, INDEX_VALUE, \
    INDEX_UNIT, INDEX_DELAY, UPDATE_THRESHOLD

updates = {}
currently_updating = set()

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
    print("initialized")
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
    from pprint import pprint
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
                for att in dir(sensor):
                    print(att, getattr(sensor, att))
                parse_sensor(sensor, hardware_index=h, sensor_index=s)

        if len(hardware.SubHardware):
            cprint(COLORS.RED, "SubHardware:")
            for sh, sub_hardware in enumerate(hardware.SubHardware):
                sub_hardware.Update()
                cprint(COLORS.BRIGHT_MAGENTA, "Sensors:")
                for s, sensor in enumerate(sub_hardware.Sensors):
                    parse_sensor(sensor, hardware_index=h, sub_hardware_index=sh, sensor_index=s)
        print("")


def reset_updates():
    updates.clear()


def bob(handle, requested_sensors):
    data = []
    for sensor_data in requested_sensors:
        if sensor_data[INDEX_SUB_HARDWARE]:
            pass
        else:
            data.append(get_sensor_value(handle, sensor_data))
    return data


async def upd(handle, h_id, delay):
    global updates
    cprint(COLORS.RED, "Checking if hardware {} needs update".format(h_id))
    try:
        cprint(COLORS.GREEN, "Time since last update:", time.time() - updates[(h_id, None)])
        cprint(COLORS.GREEN, "Time since last update (wuth threshold):", time.time() - updates[(h_id, None)] + UPDATE_THRESHOLD)
        cprint(COLORS.BRIGHT_GREEN, "Delay accepted:", delay)
        if time.time() - updates[(h_id, None)] + UPDATE_THRESHOLD >= delay:
            cprint(COLORS.RED, "HARDWARE {} NEEDS UPDATE".format(h_id))
            await real_update(handle, h_id)
        else:
            cprint(COLORS.RED, "SKIPPING UPDATE FOR {}".format(h_id))
    except KeyError:
        cprint(COLORS.RED, "HARDWARE {} NEEDS UPDATE".format(h_id))
        await real_update(handle, h_id)


async def real_update(handle, h_id):
    print("upd:", h_id, time.time())
    tuple = (h_id, None)
    if tuple in currently_updating:
        print("waiting for other request:", h_id)
        while tuple in currently_updating:
            await asyncio.sleep(0.1)
        print("other request finished:", h_id)
    else:
        currently_updating.add(tuple)
        begin = time.time()
        handle.Hardware[h_id].Update()
        updates[tuple] = time.time()
        currently_updating.remove(tuple)
        cprint(COLORS.YELLOW, "updated:", h_id, "took {} seconds".format(time.time() - begin))
    # handle.Hardware[h_id].Update()
    # print("updated:", h_id)


def up(handle, h_id):
    begin = time.time()
    if (h_id == 99):
        cprint(COLORS.BLUE, "h_id 99 stalling")
        time.sleep(5)
        cprint(COLORS.BLUE, "h_id 99 finished stalling")
    else:
        cprint(COLORS.CYAN, "upd:", h_id)
        handle.Hardware[h_id].Update()
    cprint(COLORS.YELLOW, "updated:", h_id, "took {} seconds".format(time.time() - begin))


def get_sensor_value(handle, sensor_data):
    if sensor_data[INDEX_SUB_HARDWARE]:
        sensor = None
    else:
        sensor = handle.Hardware[sensor_data[INDEX_HARDWARE]].Sensors[sensor_data[INDEX_SENSOR]]

    # tuple = (sensor_data[INDEX_HARDWARE], sensor_data[INDEX_SUB_HARDWARE])
    # if tuple not in updates:
    #     if sensor_data[INDEX_SUB_HARDWARE]:
    #         handle.Hardware[sensor_data[INDEX_HARDWARE]].SubHardware[sensor_data[INDEX_SUB_HARDWARE]].Update()
    #     else:
    #         # handle.Hardware[sensor_data[INDEX_HARDWARE]].Update()
    #         up(handle, sensor_data)
    #     updates.append(tuple)

    # handle.Hardware[sensor_data[INDEX_HARDWARE]].Update()
    # sensor_data.insert(INDEX_VALUE, sensor.Value)
    # sensor_data.insert(INDEX_UNIT, SENSORS[sensor.SensorType].unit)
    from pprint import pprint
    return {
        INDEX_HARDWARE: sensor_data[INDEX_HARDWARE],
        INDEX_SUB_HARDWARE: sensor_data[INDEX_SUB_HARDWARE],
        INDEX_SENSOR: sensor_data[INDEX_SENSOR],
        INDEX_DELAY: sensor_data[INDEX_DELAY],
        INDEX_VALUE: sensor.Value,
        INDEX_UNIT: SENSORS[sensor.SensorType].unit,
    }



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
