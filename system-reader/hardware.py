# noinspection PyPackageRequirements
from concurrent.futures._base import Future
import concurrent.futures
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Dict, Set, Tuple, List, TYPE_CHECKING, Union

import clr  # From package "pythonnet", not package "clr"
# from pythonnet import clr  # Not working, got to use line above
import os
import sys
import asyncio
import glob
import time
from pyrotools.console import cprint, COLORS
from collections import defaultdict

from websockets import WebSocketClientProtocol

if TYPE_CHECKING:
    from communication import Server
from constants import HARDWARE_TYPES, SENSORS, INDEX_HARDWARE, INDEX_SENSOR, INDEX_SUB_HARDWARE, INDEX_VALUE, \
    INDEX_UNIT, INDEX_DELAY, UPDATE_THRESHOLD

from collections.abc import Mapping


class HardwareMonitor:
    handle = None
    update_times = {}
    executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=3)
    futures: Dict[Tuple[int, int], Future] = {}

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

    async def update_if_needed(self, server: 'Server', websocket: WebSocketClientProtocol, sensor: List[Union[int, str]]):
        h_id = sensor[INDEX_HARDWARE]
        sh_id = sensor[INDEX_SUB_HARDWARE]
        delay = sensor[INDEX_DELAY]
        cprint(COLORS.RED, f"Checking if hardware ({h_id},{sh_id}) needs update")
        if (h_id, sh_id) in self.update_times:
            cprint(COLORS.GREEN, "Time since last update:", time.time() - self.update_times[(h_id, sh_id)])
            cprint(COLORS.GREEN, "Time since last update (with threshold):",
                   time.time() - self.update_times[(h_id, sh_id)] + UPDATE_THRESHOLD)
            cprint(COLORS.BRIGHT_GREEN, "Delay accepted:", delay)
            if time.time() - self.update_times[(h_id, sh_id)] + UPDATE_THRESHOLD >= delay:
                cprint(COLORS.RED, f"HARDWARE ({h_id},{sh_id}) NEEDS UPDATE")
                await self.create_update_callback(server, websocket, sensor)
            else:
                cprint(COLORS.RED, f"SKIPPING UPDATE FOR ({h_id},{sh_id})")
                server.callback(websocket=websocket, sensor=sensor)
        else:
            cprint(COLORS.RED, f"HARDWARE ({h_id},{sh_id}) FIRST UPDATE")
            await self.create_update_callback(server, websocket, sensor)

    async def create_update_callback(self, server: 'Server', websocket: WebSocketClientProtocol, sensor: List[Union[int, str]]):
        h_id = sensor[INDEX_HARDWARE]
        sh_id = sensor[INDEX_SUB_HARDWARE]
        print("create_update_task:", h_id, time.time())
        tuple = (h_id, sh_id)
        if tuple in self.futures and self.futures[tuple].running():
            print(f"Future ({tuple[0]}, {tuple[1]}) EXISTS!! Waiting for result from other request: ", h_id)
            while self.futures[tuple].running():
                await asyncio.sleep(0.1)
                server.callback(websocket=websocket, sensor=sensor)
            print(f"other request finished: ({h_id},{sh_id})")
        else:
            cprint(COLORS.MAGENTA, f"Future ({tuple[0]}, {tuple[1]}) doesn't exist")
            self.futures[tuple] = self.executor.submit(self.updater_thread, websocket=websocket, sensor=sensor)
            self.futures[tuple].add_done_callback(server.callback)
            cprint(COLORS.MAGENTA, f"submit and created future ({tuple[0]}, {tuple[1]})")

            cprint(COLORS.YELLOW, f"got update from other future: ({h_id},{sh_id})")

    def updater_thread(self, websocket: WebSocketClientProtocol, sensor: List[Union[int, str]] = None):
        # print("Executing our Task on Process {}".format(os.getpid()))
        begin = time.time()
        h_id = sensor[INDEX_HARDWARE]
        sh_id = sensor[INDEX_SUB_HARDWARE]
        if h_id == 99:
            cprint(COLORS.BLUE, "h_id 99 stalling")
            time.sleep(5)
            cprint(COLORS.BLUE, "h_id 99 finished stalling")
        else:
            cprint(COLORS.CYAN, f"update_thread: ({h_id},{sh_id})")
            if sh_id:
                self.handle.Hardware[h_id].SubHardware[sh_id].Update()
            else:
                self.handle.Hardware[h_id].Update()
        self.update_times[(h_id, sh_id)] = time.time()
        cprint(COLORS.YELLOW, f"updated: ({h_id},{sh_id}), took {time.time() - begin} seconds")
        return {
            "websocket": websocket,
            "sensor": sensor,
        }

    def get_sensor_value(self, requested_sensor: List[Union[int, str]]):
        if requested_sensor[INDEX_SUB_HARDWARE]:
            sensor = self.handle.Hardware[requested_sensor[INDEX_HARDWARE]].SubHardware[requested_sensor[INDEX_SUB_HARDWARE]].Sensors[
                requested_sensor[INDEX_SENSOR]]
        else:
            sensor = self.handle.Hardware[requested_sensor[INDEX_HARDWARE]].Sensors[requested_sensor[INDEX_SENSOR]]

        return {
            INDEX_HARDWARE: requested_sensor[INDEX_HARDWARE],
            INDEX_SUB_HARDWARE: requested_sensor[INDEX_SUB_HARDWARE],
            INDEX_SENSOR: requested_sensor[INDEX_SENSOR],
            INDEX_DELAY: requested_sensor[INDEX_DELAY],
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
