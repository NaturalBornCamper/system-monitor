"""
This uses StackOverflow answer: https://stackoverflow.com/a/49909330/1046013
Same as using_openhardwaremonitor1.py, however it also uses CPUThermometer, which is a sort of fork of OpenHardwareMonitor
However, CPU Thermometer's dll seems to be 32bits (Even if website says both are included), so it won't load on
Python 64 bits. It's not needed anyways as it doesn't give any additional info after OpenHardwareMonitor
"""
import json
from pprint import pprint

from pyrotools.console import cprint, COLORS

import asyncio
import datetime
import random
import websockets

import hardware


async def time(websocket, path):
    while True:
        data = {
            "cpu": {
                "temperature": 40,
                "usage": "50%"
            },
            "memory": {
                "temperature": 50,
                "usage": "20%"
            },
        }
        serialized_data = json.dumps(data)
        cprint(COLORS.CYAN, serialized_data)
        try:
            await websocket.send(serialized_data)
        except websockets.exceptions.ConnectionClosed:
            # websocket.close()
            cprint(COLORS.YELLOW, "Client disconnected")
            break
        await asyncio.sleep(1)

if __name__ == "__main__":
    LibreHardwareHandle = hardware.initialize_librehardwaremonitor()
    hardware.fetch_stats(LibreHardwareHandle)

    start_server = websockets.serve(time, "127.0.0.1", 2346)
    cprint(COLORS.CYAN, "Listening on port 2346")

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
