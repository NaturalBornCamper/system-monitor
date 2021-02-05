import asyncio
import json
from typing import List

import websockets
from pyrotools.console import cprint, COLORS
from constants import ERROR_ADMIN, INDEX_SUB_HARDWARE, INDEX_HARDWARE, INDEX_DELAY
from concurrent.futures._base import Future
import concurrent.futures

from hardware import HardwareMonitor


class Server:
    # monitor = None
    monitor: HardwareMonitor = None
    tasks = {}
    datas = []
    requested_sensors = [
        [1, None, 4, 0.5],  # CPU Load
        [1, None, 9, 3],  # CPU Temp
        [2, None, 2, 0.5],  # Memory Load
        [3, None, 0, 3],  # GPU Temp
        [3, None, 4, 1],  # GPU Core Load
        [3, None, 6, 1],  # GPU Video Engine Load
        [3, None, 11, 1],  # GPU Memory Load
        [4, None, 3, 1],  # Seagate HDD Load
        [4, None, 0, 1],  # Seagate Temp
        [5, None, 2, 1],  # HGST Load
        [6, None, 0, 1],  # SSD Temp
        [6, None, 6, 1],  # SSD Temp 1
        [6, None, 7, 1],  # SSD Temp 2
        [6, None, 10, 1],  # SSD Load
        [13, None, 2, 1],  # Wi-Fi Upload
        [13, None, 3, 1],  # Wi-Fi Download
        [13, None, 4, 1],  # Wi-Fi Load
    ]

    def __init__(self, hardware_monitor):
        self.monitor = hardware_monitor
        start_server = websockets.serve(self.serve_new_client, "127.0.0.1", 2346)
        cprint(COLORS.CYAN, "Listening on port 2346")

        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    async def periodic(self, sensor: List = None):
        while True:
            await self.monitor.upd(sensor, self)
            # print('periodic')
            # self.datas.append(self.monitor.get_sensor_value(sensor))
            await asyncio.sleep(sensor[INDEX_DELAY])

    def cancel_all_websocket_tasks(self, websocket):
        if websocket.local_address[0] in self.tasks:
            for task_ in self.tasks[websocket.local_address[0]]:
                task_.cancel()

    async def serve_new_client(self, websocket, path):
        print("New client connected")
        if websocket.local_address[0] not in self.tasks.keys():
            self.tasks[websocket.local_address[0]] = []
        else:
            self.cancel_all_websocket_tasks(websocket)

        for sensor in self.requested_sensors:
            self.tasks[websocket.local_address[0]].append(asyncio.create_task(self.periodic(
                sensor=sensor
            )))
        while True:
            if self.datas:
                serialized_data = json.dumps(self.datas)

                cprint(COLORS.CYAN, serialized_data)
                try:
                    # await websocket.send("yo")
                    await websocket.send(serialized_data)
                    self.datas = []
                except websockets.exceptions.ConnectionClosed:
                    # websocket.close()
                    self.cancel_all_websocket_tasks(websocket)
                    cprint(COLORS.YELLOW, "Client disconnected")
                    break
            # await asyncio.sleep(1)
            await asyncio.sleep(0.5)

    def callback(self, fut: Future):
        sensor = fut.result()
        self.datas.append(self.monitor.get_sensor_value(sensor_data=sensor))
        cprint(COLORS.RED, "thread finished")
