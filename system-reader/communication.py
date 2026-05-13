import asyncio
import json
from pprint import pprint
from typing import List, Set, Dict, Union

import socket
from datetime import datetime
from pathlib import Path
from pyrotools.console import cprint, COLORS
from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosed
from websockets.protocol import State

from constants import WEBSOCKET_BROADCAST_DELAY_SECONDS, Actions, Sensor
from concurrent.futures._base import Future
import concurrent.futures

from hardware import HardwareMonitor
from typing import TYPE_CHECKING
from asyncio.tasks import Task


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
    clients: Dict[ServerConnection, Client] = {}
    log_dir: Path = None

    # TODO Not sure how come we have a requested_sensors here since they are normally requested by the client, but I don't like that they are just indexes without keys her. Should be at least a dict. Fix this
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
        # Keep per-client logs in a dedicated folder.
        self.log_dir = Path("logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        # Clear per-client logs on startup to keep writes append-only.
        for log_file in self.log_dir.glob("*.log"):
            try:
                log_file.unlink()
            except OSError:
                pass

        # Get host IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()

        self.monitor = hardware_monitor
        asyncio.run(self.serve_forever(ip, 2346))
        # asyncio.run(self.serve_forever("127.0.0.1", 2346))

    async def serve_forever(self, ip: str, port: int) -> None:
        cprint(COLORS.CYAN, f"Listening on port {port}")
        async with serve(self.serve_new_client, ip, port) as websocket_server:
            await websocket_server.serve_forever()

    async def broadcast(self, websocket: ServerConnection) -> None:
        while True:
            # If the client is already removed, exit quietly.
            if websocket not in self.clients:
                return
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
                except ConnectionClosed:
                    cprint(COLORS.YELLOW, "Client disconnected (found out while sending data)")
                    return await self.disconnect_client(websocket)
            # TODO Should specific broadcast delay be requested by client instead?
            await asyncio.sleep(WEBSOCKET_BROADCAST_DELAY_SECONDS)

    async def disconnect_client(self, websocket: ServerConnection) -> None:
        if client := self.clients.pop(websocket, None):
            # Log disconnects to a file to help track hibernate/reconnect cleanup.
            self.log_event(
                websocket,
                f"Disconnect cleanup (clients left: {len(self.clients)})"
            )
            # TODO Check if any threads were going to send back data to callback for websocket sending
            client.cancel_all_hardware_tasks()
            if client.broadcast_task and not client.broadcast_task.done():
                client.broadcast_task.cancel()
        await websocket.close()

    async def periodic(self, websocket: ServerConnection, sensor: List[Union[int, str]]) -> None:
        while True:
            await self.monitor.update_if_needed(self, websocket, sensor=sensor)
            # print('periodic sensor', sensor[Sensor.HARDWARE], sensor[Sensor.SUB_HARDWARE], sensor[Sensor.SENSOR])
            # pprint(self.clients[websocket].hardware_tasks)
            await asyncio.sleep(sensor[Sensor.DELAY])

    async def serve_new_client(self, websocket: ServerConnection) -> None:
        print(f"New client connected {websocket.remote_address}: ", websocket)
        self.clients[websocket] = Client()
        self.clients[websocket].broadcast_task = asyncio.create_task(self.broadcast(websocket))
        self.log_event(websocket, "Client connected")

        # TODO Bug: Exception on line 120 when computer resuming from hibernation (Because client disappeared maybe)
        try:
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
        finally:
            # Always clean up client state, even on abrupt disconnects.
            await self.disconnect_client(websocket)

    def log_event(self, websocket: ServerConnection, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_path = self.get_log_path(websocket)
        line = f"{timestamp} {message}\n"
        # Append-only logging for low overhead.
        with log_path.open("a", encoding="utf-8", errors="ignore") as handle:
            handle.write(line)

    def get_log_path(self, websocket: ServerConnection) -> Path:
        # Build a filename from the remote address; fall back to "unknown" if missing.
        remote = "unknown"
        if websocket and websocket.remote_address:
            host, port = websocket.remote_address
            remote = f"{host}"
        safe_remote = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(remote))
        return self.log_dir / f"{safe_remote}.log"

    def callback(self, future: Future = None, websocket: ServerConnection = None, sensor: List = None) -> None:
        if future:
            # cprint(COLORS.BRIGHT_YELLOW, "Future running?", future.running())
            websocket = future.result()['websocket']
            sensor = future.result()['sensor']

        # Check to make sure websocket still exists in case it was disconnected before update thread ended
        if websocket in self.clients:
            self.clients[websocket].sensor_data.append(self.monitor.get_sensor_value(requested_sensor=sensor))

        # cprint(COLORS.RED, "thread finished")
