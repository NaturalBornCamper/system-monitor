import ctypes
import sys

from pyrotools.console import cprint, COLORS

from communication import Server
from constants import ERROR_ADMIN
from hardware import HardwareMonitor

LibreHardwareHandle = None


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


if __name__ == "__main__":
    # if not is_admin():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        cprint(COLORS.RED, "You need administrator rights to run the hardware_monitor")
        sys.exit(ERROR_ADMIN)

    # Server code below
    hardware_monitor = HardwareMonitor()
    hardware_monitor.fetch_stats()
    server = Server(hardware_monitor=hardware_monitor)
    print("END")
