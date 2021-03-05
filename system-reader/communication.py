import asyncio
import json
from pprint import pprint
from typing import List, Set, Dict, Union

import socket
import websockets
from pyrotools.console import cprint, COLORS
from websockets.protocol import State

from constants import WEBSOCKET_BROADCAST_DELAY_SECONDS, Actions, Sensor
from concurrent.futures._base import Future
import concurrent.futures

from hardware import HardwareMonitor
from typing import TYPE_CHECKING
from asyncio.tasks import Task

# Doesn't work anymore, says "'WebSocketClientProtocol' is not defined" with TYPE CHECKING, must absolutely import WebSocketClientProtocol
# if TYPE_CHECKING:
#     from websockets import WebSocketClientProtocol
from websockets import WebSocketClientProtocol


class Client:
    hardware_tasks: List[Task]
    sensor_data: List[Dict[str, Union[int, float, str]]]
    broadcast_task: Task = None

    # Note: Need to create new lists in constructor, or they will share reference to same list
    def __init__(self):
        self.hardware_tasks = []
        self.sensor_data = []

    def cancel_all_hardware_tasks(self) -> None:
        for task in self.hardware_tasks:
            task.cancel()
        self.hardware_tasks.clear()


class Server:
    monitor: HardwareMonitor = None
    clients: Dict[WebSocketClientProtocol, Client] = {}

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
        # Get host IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()

        self.monitor = hardware_monitor
        start_server = websockets.serve(self.serve_new_client, ip, 2346)
        # start_server = websockets.serve(self.serve_new_client, "127.0.0.1", 2346)
        cprint(COLORS.CYAN, "Listening on port 2346")

        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    async def broadcast(self, websocket: WebSocketClientProtocol) -> None:
        while True:
            if websocket.state == State.CLOSED:
                cprint(COLORS.YELLOW, "Client disconnected (found out during broadcast iteration)")
                return await self.disconnect_client(websocket)
            if self.clients[websocket].sensor_data:
                serialized_data = json.dumps(self.clients[websocket].sensor_data)
                self.clients[websocket].sensor_data.clear()

                print('---------------------SEND--------------------')
                cprint(COLORS.CYAN, serialized_data)
                try:
                    await websocket.send(serialized_data)
                except websockets.exceptions.ConnectionClosed:
                    # except websockets.exceptions.ConnectionClosedError:
                    cprint(COLORS.YELLOW, "Client disconnected (found out while sending data)")
                    return await self.disconnect_client(websocket)
            # TODO Should specific broadcast delay be requested by client instead?
            await asyncio.sleep(WEBSOCKET_BROADCAST_DELAY_SECONDS)

    async def disconnect_client(self, websocket: WebSocketClientProtocol) -> None:
        if client := self.clients.pop(websocket, None):
            # TODO Check if any threads were going to send back data to callback for websocket sending
            client.cancel_all_hardware_tasks()
            client.broadcast_task.cancel()
        await websocket.close()

    async def periodic(self, websocket: WebSocketClientProtocol, sensor: List[Union[int, str]]) -> None:
        while True:
            await self.monitor.update_if_needed(self, websocket, sensor=sensor)
            print('periodic sensor', sensor[Sensor.HARDWARE], sensor[Sensor.SUB_HARDWARE], sensor[Sensor.SENSOR])
            pprint(self.clients[websocket].hardware_tasks)
            await asyncio.sleep(sensor[Sensor.DELAY])

    async def serve_new_client(self, websocket: WebSocketClientProtocol, path: str) -> None:
        print("New client connected: ", websocket)
        self.clients[websocket] = Client()
        self.clients[websocket].broadcast_task = asyncio.create_task(self.broadcast(websocket))

        async for message in websocket:
            print('-------------------------MESSAGE RECEIVED----------------------------')
            data = json.loads(message)
            pprint(data)
            if 'action' in data and data['action'] == Actions.SET_SENSORS:
                self.clients[websocket].cancel_all_hardware_tasks()
                for sensor in data['requested_sensors']:
                    self.clients[websocket].hardware_tasks.append(asyncio.create_task(self.periodic(
                        websocket=websocket,
                        sensor=sensor
                    )))
                print(self.clients[websocket].hardware_tasks)

    def callback(self, future: Future = None, websocket: WebSocketClientProtocol = None, sensor: List = None) -> None:
        if future:
            cprint(COLORS.BRIGHT_YELLOW, "Future running?", future.running())
            websocket = future.result()['websocket']
            sensor = future.result()['sensor']

        # Check to make sure websocket still exists in case it was disconnected before update thread ended
        if websocket in self.clients:
            self.clients[websocket].sensor_data.append(self.monitor.get_sensor_value(requested_sensor=sensor))

        cprint(COLORS.RED, "thread finished")
