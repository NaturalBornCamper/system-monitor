# noinspection PyPackageRequirements
from concurrent.futures._base import Future
import concurrent.futures
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Dict, Set, Tuple, List

import clr  # From package "pythonnet", not package "clr"
# from pythonnet import clr  # Not working, got to use line above
import os
import sys
import asyncio
import glob
import time
from pyrotools.console import cprint, COLORS
from collections import defaultdict

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from communication import Server
from constants import HARDWARE_TYPES, SENSORS, INDEX_HARDWARE, INDEX_SENSOR, INDEX_SUB_HARDWARE, INDEX_VALUE, \
    INDEX_UNIT, INDEX_DELAY, UPDATE_THRESHOLD


class HardwareMonitor:
    handle = None
    updates = {}
    currently_updating: Set[Tuple] = set()
    executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=3)
    futures: Dict[Tuple, Future] = {}

    def __init__(self):
        file = 'lib/LibreHardwareMonitorLib.dll'
        # clr.AddReference(file)
        clr.AddReference(os.path.abspath(os.path.dirname(__file__)) + R'\lib/LibreHardwareMonitorLib.dll')
        # clr.AddReference(os.path.abspath(os.path.dirname(__file__)) + R'\lib/HidSharp.dll')

        # noinspection PyUnresolvedReferences
        from LibreHardwareMonitor import Hardware

        self.handle = Hardware.Computer()
        self.handle.IsCpuEnabled = True
        self.handle.IsGpuEnabled = True
        self.handle.IsMemoryEnabled = True
        self.handle.IsMotherboardEnabled = True
        self.handle.IsControllerEnabled = True
        self.handle.IsNetworkEnabled = True
        self.handle.IsStorageEnabled = True

        self.handle.Open()
        print("initialized")

    def __del__(self):
        self.executor.shutdown(cancel_futures=True)

    def task(self, sensor: List = None):
        # print("Executing our Task on Process {}".format(os.getpid()))
        begin = time.time()
        h_id = sensor[INDEX_HARDWARE]
        if (h_id == 99):
            cprint(COLORS.BLUE, "h_id 99 stalling")
            time.sleep(5)
            cprint(COLORS.BLUE, "h_id 99 finished stalling")
        else:
            cprint(COLORS.CYAN, "upd:", h_id)
            self.handle.Hardware[h_id].Update()
        self.updates[(h_id, None)] = time.time()
        cprint(COLORS.YELLOW, "updated:", h_id, "took {} seconds".format(time.time() - begin))
        return sensor

    async def upd(self, sensor: List, server: 'Server'):
        h_id = sensor[INDEX_HARDWARE]
        delay = sensor[INDEX_DELAY]
        cprint(COLORS.RED, "Checking if hardware {} needs update".format(h_id))
        try:
            cprint(COLORS.GREEN, "Time since last update:", time.time() - self.updates[(h_id, None)])
            cprint(COLORS.GREEN, "Time since last update (with threshold):",
                   time.time() - self.updates[(h_id, None)] + UPDATE_THRESHOLD)
            cprint(COLORS.BRIGHT_GREEN, "Delay accepted:", delay)
            if time.time() - self.updates[(h_id, None)] + UPDATE_THRESHOLD >= delay:
                cprint(COLORS.RED, "HARDWARE {} NEEDS UPDATE".format(h_id))
                await self.real_update(sensor, server)
            else:
                cprint(COLORS.RED, "SKIPPING UPDATE FOR {}".format(h_id))
        except KeyError:
            cprint(COLORS.RED, "HARDWARE {} FIRST UPDATE".format(h_id))
            await self.real_update(sensor, server)

    async def real_update(self, sensor: List, server: 'Server'):
        h_id = sensor[INDEX_HARDWARE]
        print("upd:", h_id, time.time())
        tuple = (h_id, None)
        if tuple in self.futures and self.futures[tuple].running():
            print("waiting for other request:", h_id)
            while self.futures[tuple].running():
                await asyncio.sleep(0.1)
                server.callback(sensor=sensor)
            print("other request finished:", h_id)
        else:
            cprint(COLORS.MAGENTA, "submit")
            self.futures[tuple] = self.executor.submit(self.task, sensor=sensor)
            self.futures[tuple].add_done_callback(server.callback)

            begin = time.time()
            # time.sleep(4)
            cprint(COLORS.YELLOW, "updated:", h_id, "took {} seconds".format(time.time() - begin))

    def get_sensor_value(self, sensor_data: List):
        if sensor_data[INDEX_SUB_HARDWARE]:
            sensor = self.handle.Hardware[sensor_data[INDEX_HARDWARE]].SubHardware[INDEX_SUB_HARDWARE].Sensors[
                sensor_data[INDEX_SENSOR]]
        else:
            sensor = self.handle.Hardware[sensor_data[INDEX_HARDWARE]].Sensors[sensor_data[INDEX_SENSOR]]

        return {
            INDEX_HARDWARE: sensor_data[INDEX_HARDWARE],
            INDEX_SUB_HARDWARE: sensor_data[INDEX_SUB_HARDWARE],
            INDEX_SENSOR: sensor_data[INDEX_SENSOR],
            INDEX_DELAY: sensor_data[INDEX_DELAY],
            INDEX_VALUE: sensor.Value,
            INDEX_UNIT: SENSORS[sensor.SensorType].unit,
        }

    def fetch_stats(self):
        for h, hardware in enumerate(self.handle.Hardware):
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
                    self.parse_sensor(sensor, hardware_index=h, sensor_index=s)

            if len(hardware.SubHardware):
                cprint(COLORS.RED, "SubHardware:")
                for sh, sub_hardware in enumerate(hardware.SubHardware):
                    sub_hardware.Update()
                    cprint(COLORS.BRIGHT_MAGENTA, "Sensors:")
                    for s, sensor in enumerate(sub_hardware.Sensors):
                        self.parse_sensor(sensor, hardware_index=h, sub_hardware_index=sh, sensor_index=s)
            print("")

    def parse_sensor(self, sensor, hardware_index: int, sub_hardware_index: int = None, sensor_index: int = None):
        if sensor.Value is not None:
            cprint(
                COLORS.GREEN,
                "TYPE: {}, NAME: {}, VALUE: {} {}, [HARDWARE, SUB-HARDWARE, SENSOR] = [{}, {}, {}]".format(
                    SENSORS[sensor.SensorType].name,
                    sensor.Name,
                    sensor.Value,
                    SENSORS[sensor.SensorType].unit,
                    hardware_index,
                    sub_hardware_index,
                    sensor_index,
                )
            )
