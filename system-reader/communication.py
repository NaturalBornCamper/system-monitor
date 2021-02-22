import asyncio
import json
from typing import List, Set, Dict, Union

import websockets
from pyrotools.console import cprint, COLORS
from constants import ERROR_ADMIN, INDEX_SUB_HARDWARE, INDEX_HARDWARE, INDEX_DELAY, INDEX_SENSOR
from concurrent.futures._base import Future
import concurrent.futures

from hardware import HardwareMonitor
from typing import TYPE_CHECKING
from asyncio.tasks import Task

# Doesn't work anymore, says "'WebSocketClientProtocol' is not defined" with TYPE CHECKING, must absolutely import WebSocketClientProtocol
# if TYPE_CHECKING:
#     from websockets import WebSocketClientProtocol
from websockets import WebSocketClientProtocol


class Server:
    # monitor = None
    monitor: HardwareMonitor = None
    tasks: Dict[str, List[Task]] = {}
    bob: Task = None
    datas: Dict[str, List[str]] = {}
    # datas: Set[WebSocketClientProtocol, List] = []
    requested_sensors: List[Union[int, str]] = [
        [1, None, 4, 1],  # CPU Load
        [1, None, 9, 3],  # CPU Temp
        # [2, None, 2, 3],  # Memory Load
        # [3, None, 0, 3],  # GPU Temp
        # [3, None, 4, 1],  # GPU Core Load
        # [3, None, 6, 1],  # GPU Video Engine Load
        # [3, None, 11, 1],  # GPU Memory Load
        # [4, None, 3, 1],  # Seagate HDD Load
        # [4, None, 0, 1],  # Seagate Temp
        # [5, None, 2, 1],  # HGST Load
        # [6, None, 0, 1],  # SSD Temp
        # [6, None, 6, 1],  # SSD Temp 1
        # [6, None, 7, 1],  # SSD Temp 2
        # [6, None, 10, 1],  # SSD Load
        # [13, None, 2, 1],  # Wi-Fi Upload
        # [13, None, 3, 1],  # Wi-Fi Download
        # [13, None, 4, 1],  # Wi-Fi Load
    ]

    def __init__(self, hardware_monitor: HardwareMonitor):
        self.monitor = hardware_monitor
        start_server = websockets.serve(self.serve_new_client, "127.0.0.1", 2346)
        cprint(COLORS.CYAN, "Listening on port 2346")

        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    async def periodic(self, websocket: WebSocketClientProtocol, sensor: List[Union[int, str]] = None):
        while True:
            await self.monitor.update_if_needed(self, websocket, sensor=sensor)
            print('periodic sensor', sensor[INDEX_HARDWARE], sensor[INDEX_SUB_HARDWARE], sensor[INDEX_SENSOR])
            from pprint import pprint
            pprint(self.tasks)
            await asyncio.sleep(sensor[INDEX_DELAY])

    def cancel_all_websocket_tasks(self, websocket: WebSocketClientProtocol):
        if websocket.local_address[0] in self.tasks:
            for task in self.tasks[websocket.local_address[0]]:
                task.cancel()

    async def serve_new_client(self, websocket: WebSocketClientProtocol, path):
        print("New client connected")
        if websocket.local_address[0] not in self.tasks.keys():
            self.tasks[websocket.local_address[0]] = []
        else:
            self.cancel_all_websocket_tasks(websocket)

        for sensor in self.requested_sensors:
            from pprint import pprint
            pprint(sensor)
            self.tasks[websocket.local_address[0]].append(asyncio.create_task(self.periodic(
                websocket=websocket,
                sensor=sensor
            )))
        print(self.tasks)
        while True:
            if data := self.datas.pop(websocket.local_address[0], None):
                serialized_data = json.dumps(data)

                cprint(COLORS.CYAN, serialized_data)
                try:
                    # await websocket.send("yo")
                    await websocket.send(serialized_data)
                except websockets.exceptions.ConnectionClosed:
                    # websocket.close()
                    self.cancel_all_websocket_tasks(websocket)
                    cprint(COLORS.YELLOW, "Client disconnected")
                    break
            # await asyncio.sleep(1)
            await asyncio.sleep(0.5)

    def callback(self, fut: Future = None, websocket: WebSocketClientProtocol = None, sensor: List = None):
        if fut:
            cprint(COLORS.BRIGHT_YELLOW, "Future running?", fut.running())
            websocket = fut.result()["websocket"]
            sensor = fut.result()["sensor"]

        if websocket.local_address[0] not in self.datas:
            self.datas[websocket.local_address[0]] = []

        self.datas[websocket.local_address[0]].append(self.monitor.get_sensor_value(sensor_data=sensor))

        cprint(COLORS.RED, "thread finished")
