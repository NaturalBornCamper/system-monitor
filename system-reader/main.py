"""
This uses StackOverflow answer: https://stackoverflow.com/a/49909330/1046013
Same as using_openhardwaremonitor1.py, however it also uses CPUThermometer, which is a sort of fork of OpenHardwareMonitor
However, CPU Thermometer's dll seems to be 32bits (Even if website says both are included), so it won't load on
Python 64 bits. It's not needed anyways as it doesn't give any additional info after OpenHardwareMonitor
"""
from random import random

import clr  # From package "pythonnet", not package "clr"
import asyncio
import ctypes
import json
import sys
import os
from multiprocessing import Process, Manager
from multiprocessing.managers import BaseManager
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor

import concurrent.futures

import websockets
from pyrotools.console import cprint, COLORS

import hardware
from constants import ERROR_ADMIN, INDEX_SUB_HARDWARE, INDEX_HARDWARE, INDEX_DELAY

LibreHardwareHandle = None


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


"""
1 DIM
+simple copy-paste from console for config
+compact to read

STRUCTURE 1
+no compatibility issues
+Can easily add attributes
+Ensures no duplicate hardware or sub hardware
-Heavy to read

STRUCTURE 2
-Compatibility issues with json, need to add extra steps somehow
+Not too bad to read
"""
# requested_sensors = [
#     {
#         "hardware_id": 1,
#         "sub_hardware_id": None,
#         "sensors": [
#             {
#                 "sensor_id": 4,
#                 "Name": "CPU Load",
#             },
#             {
#                 "sensor_id": 9,
#                 "Name": "CPU Temp",
#             },
#         ]
#     }
# ]
# requested_sensors = {
#     1: {
#         None: {
#             [4, "CPU Load"],
#             [9, "CPU Temp"],
#         }
#     }
# }

requested_sensors = [
    [1, None, 4, 1],  # CPU Load
    [1, None, 9, 3],  # CPU Temp
    [2, None, 2, 1],  # Memory Load
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
computed_data = [
    [1, None, 4, 30.5, "%"],  # CPU Load
    [1, None, 9],  # CPU Temp
    [2, None, 2],  # Memory Load
    [3, None, 0],  # GPU Temp
    [3, None, 4],  # GPU Core Load
    [3, None, 6],  # GPU Video Engine Load
    [3, None, 11],  # GPU Memory Load
    [4, None, 3],  # Seagate HDD Load
    [4, None, 0],  # Seagate Temp
    [5, None, 2],  # HGST Load
    [6, None, 0],  # SSD Temp
    [6, None, 6],  # SSD Temp 1
    [6, None, 7],  # SSD Temp 2
    [6, None, 10],  # SSD Load
    [13, None, 2],  # Wi-Fi Upload
    [13, None, 3],  # Wi-Fi Download
    [13, None, 4],  # Wi-Fi Load
]

tasks = {}
datas = []
async def periodic(sensor=None):
    global LibreHardwareHandle
    while True:
        await hardware.upd(LibreHardwareHandle, sensor[INDEX_HARDWARE], sensor[INDEX_DELAY])
        # print('periodic')
        datas.append(hardware.get_sensor_value(LibreHardwareHandle, sensor))
        await asyncio.sleep(sensor[INDEX_DELAY])

def cancel_all_websocket_tasks(websocket):
    if websocket.local_address[0] in tasks:
        for task_ in tasks[websocket.local_address[0]]:
            task_.cancel()


async def serve_new_client(websocket, path):
    global datas, tasks
    if websocket.local_address[0] not in tasks.keys():
        tasks[websocket.local_address[0]] = []
    else:
        cancel_all_websocket_tasks(websocket)

    for sensor in requested_sensors:
        tasks[websocket.local_address[0]].append(asyncio.create_task(periodic(
            sensor=sensor
        )))
    while True:
        if datas:
            serialized_data = json.dumps(datas)

            cprint(COLORS.CYAN, serialized_data)
            try:
                # await websocket.send("yo")
                await websocket.send(serialized_data)
                datas = []
            except websockets.exceptions.ConnectionClosed:
                # websocket.close()
                cancel_all_websocket_tasks(websocket)
                cprint(COLORS.YELLOW, "Client disconnected")
                break
        # await asyncio.sleep(1)
        await asyncio.sleep(0.00001)

if __name__ == "__main__":

    # if not is_admin():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        cprint(COLORS.RED, "You need administrator rights to run the monitor")
        sys.exit(ERROR_ADMIN)

    # BaseManager.register('SimpleClass', SimpleClass)
    LibreHardwareHandle = hardware.initialize_librehardwaremonitor()
    # Server code below
    start_server = websockets.serve(serve_new_client, "127.0.0.1", 2346)
    cprint(COLORS.CYAN, "Listening on port 2346")

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
