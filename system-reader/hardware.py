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
from constants import HARDWARE_TYPES, SENSOR_TYPES, Sensor, UPDATE_THRESHOLD

from collections.abc import Mapping


class HardwareMonitor:
    handle = None  # Hardware.Computer
    update_times: Dict[Tuple[int, int], float] = {}
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
        self.executor.shutdown(wait=False)
        # Feb 2021
        # "cancel_futures" param was added in Python 3.9, but clr wasn't compiled for Python 3.9 yet, need to wait..
        # self.executor.shutdown(wait=False, cancel_futures=True)

    async def update_if_needed(self, server: 'Server', websocket: WebSocketClientProtocol,
                               sensor: List[Union[int, str]]) -> None:
        hardware_id = sensor[Sensor.HARDWARE]
        sub_hardware_id = sensor[Sensor.SUB_HARDWARE]
        delay = sensor[Sensor.DELAY]
        # cprint(COLORS.RED, f"Checking if hardware ({hardware_id},{sub_hardware_id}) needs update")
        if (hardware_id, sub_hardware_id) in self.update_times:
            # cprint(COLORS.GREEN, "Time since last update:",
            #        time.time() - self.update_times[(hardware_id, sub_hardware_id)])
            # cprint(COLORS.GREEN, "Time since last update (with threshold):",
            #        time.time() - self.update_times[(hardware_id, sub_hardware_id)] + UPDATE_THRESHOLD)
            # cprint(COLORS.BRIGHT_GREEN, "Delay accepted:", delay)
            if time.time() - self.update_times[(hardware_id, sub_hardware_id)] + UPDATE_THRESHOLD >= delay:
                # cprint(COLORS.RED, f"HARDWARE ({hardware_id},{sub_hardware_id}) NEEDS UPDATE")
                await self.create_update_callback(server, websocket, sensor)
            else:
                # cprint(COLORS.RED, f"SKIPPING UPDATE FOR ({hardware_id},{sub_hardware_id})")
                # Another coroutine might have already started an Update() for this same hardware. If we read a sensor
                # value while Update() is running, LibreHardwareMonitor can temporarily return stale/zero values
                # (network throughput is especially sensitive to this). Waiting here ensures we read a consistent,
                # post-update snapshot when an update is in-flight.
                key = (hardware_id, sub_hardware_id)
                if key in self.futures and not self.futures[key].done():
                    await asyncio.wrap_future(self.futures[key])
                server.callback(websocket=websocket, sensor=sensor)
        else:
            # cprint(COLORS.RED, f"HARDWARE ({hardware_id},{sub_hardware_id}) FIRST UPDATE")
            await self.create_update_callback(server, websocket, sensor)

    async def create_update_callback(self, server: 'Server', websocket: WebSocketClientProtocol,
                                     sensor: List[Union[int, str]]) -> None:
        hardware_id = sensor[Sensor.HARDWARE]
        sub_hardware_id = sensor[Sensor.SUB_HARDWARE]
        # print("create_update_task:", hardware_id, time.time())
        key = (hardware_id, sub_hardware_id)
        if key not in self.futures or self.futures[key].done():
            # Ensure at most one Update() runs per (hardware_id, sub_hardware_id). Multiple sensors (ex: upload +
            # download) can point at the same "Hardware" object, so they should share the same update future.
            self.futures[key] = self.executor.submit(self.updater_thread, websocket=websocket, sensor=sensor)
            # cprint(COLORS.MAGENTA, f"submit and created future ({key[0]}, {key[1]})")

        # Important: wait for the update thread to finish, then read the sensor ONCE. The previous implementation
        # used a loop like:
        #   while future.running(): sleep(); callback()
        # That meant we kept reading sensors *during* Update(), which produced intermittent 0/spike values and
        # never guaranteed a final "fresh" reading for sensors that didn't start the update.
        # Also: we deliberately do NOT use Future.add_done_callback(server.callback) here, because that would run
        # server.callback() on the worker thread, racing with the asyncio websocket send/clear logic.
        await asyncio.wrap_future(self.futures[key])
        # print(f"other request finished: ({hardware_id},{sub_hardware_id})")
        # cprint(COLORS.YELLOW, f"got update from other future: ({hardware_id},{sub_hardware_id})")
        server.callback(websocket=websocket, sensor=sensor)

    # Note: Return type hint is a bit useless here as it will be placed in the "future" object, never
    # called directly. Left it there for reference
    def updater_thread(self, websocket: WebSocketClientProtocol, sensor: List[Union[int, str]]) \
            -> Dict[str, Union[List[Union[int, str]], WebSocketClientProtocol]]:
        # print("Executing our Task on Process {}".format(os.getpid()))
        begin = time.time()
        hardware_id = sensor[Sensor.HARDWARE]
        sub_hardware_id = sensor[Sensor.SUB_HARDWARE]
        if hardware_id == 99:
            cprint(COLORS.BLUE, "hardware_id 99 stalling")
            time.sleep(5)
            cprint(COLORS.BLUE, "hardware_id 99 finished stalling")
        else:
            # cprint(COLORS.CYAN, f"update_thread: ({hardware_id},{sub_hardware_id})")
            # sub_hardware_id can be 0 (valid index), so we must check against None explicitly.
            if sub_hardware_id is not None:
                self.handle.Hardware[hardware_id].SubHardware[sub_hardware_id].Update()
            else:
                self.handle.Hardware[hardware_id].Update()
        self.update_times[(hardware_id, sub_hardware_id)] = time.time()
        # cprint(COLORS.YELLOW, f"updated: ({hardware_id},{sub_hardware_id}), took {time.time() - begin} seconds")
        return {
            "websocket": websocket,
            "sensor": sensor,
        }

    def get_sensor_value(self, requested_sensor: List[Union[int, str]]) -> Dict[str, Union[int, float, str]]:
        hardware_id = requested_sensor[Sensor.HARDWARE]
        sub_hardware_id = requested_sensor[Sensor.SUB_HARDWARE]
        sensor_id = requested_sensor[Sensor.SENSOR]

        if sub_hardware_id is not None:
            sensor = self.handle.Hardware[hardware_id].SubHardware[sub_hardware_id].Sensors[sensor_id]
        else:
            sensor = self.handle.Hardware[hardware_id].Sensors[sensor_id]

        requested_sensor[Sensor.VALUE] = sensor.Value
        requested_sensor[Sensor.UNIT] = SENSOR_TYPES[sensor.SensorType].unit
        return requested_sensor
        # return {
        #     Sensor.ID: requested_sensor[Sensor.ID],
        #     Sensor.LABEL: requested_sensor[Sensor.LABEL],
        #     Sensor.HARDWARE: hardware_id,
        #     Sensor.SUB_HARDWARE: sub_hardware_id,
        #     Sensor.SENSOR: sensor_id,
        #     Sensor.DELAY: requested_sensor[Sensor.DELAY],
        #     Sensor.VALUE: sensor.Value,
        #     Sensor.UNIT: SENSOR_TYPES[sensor.SensorType].unit,
        # }

    def fetch_stats(self) -> None:
        # print(self.handle.Hardware[0].Sensors[23].Value)
        # print(self.handle.Hardware[0].SubHardware[0].Sensors[23])
        # print(self.handle.Hardware[0].Sensors[23])
        for h, hardware in enumerate(self.handle.Hardware):
            hardware.Update()
            cprint(COLORS.BRIGHT_BLUE, "HARDWARE TYPE: {}, NAME: {}, SUB HARDWARE COUNT: {}, SENSOR LIST ({}):".format(
                HARDWARE_TYPES[hardware.HardwareType],
                hardware.Name,
                f"{len(hardware.SubHardware)}",
                f"{len(hardware.Sensors)}"
            ))

            if len(hardware.Sensors):
                for s, sensor in enumerate(hardware.Sensors):
                    self.parse_sensor(sensor, hardware_index=h, sensor_index=s)

            if len(hardware.SubHardware):
                cprint(COLORS.RED, "SubHardware:")
                for sh, sub_hardware in enumerate(hardware.SubHardware):
                    sub_hardware.Update()
                    for s, sensor in enumerate(sub_hardware.Sensors):
                        self.parse_sensor(sensor, hardware_index=h, sub_hardware_index=sh, sensor_index=s)

    def parse_sensor(self, sensor, hardware_index: int, sub_hardware_index: int = None, sensor_index: int = None) \
            -> None:
        if sensor.Value is not None:
            cprint(
                COLORS.GREEN,
                "TYPE: {}, NAME: {}, VALUE: {} {}, {{[Sensor.HARDWARE]: {}, [Sensor.SUB_HARDWARE]: {}, [Sensor.SENSOR]: {}}}".format(
                    SENSOR_TYPES[sensor.SensorType].name,
                    sensor.Name,
                    sensor.Value,
                    SENSOR_TYPES[sensor.SensorType].unit,
                    hardware_index,
                    sub_hardware_index if sub_hardware_index is not None else "null",
                    sensor_index,
                )
            )
