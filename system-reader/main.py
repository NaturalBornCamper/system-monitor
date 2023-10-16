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


# TODO Bug: When refreshing client page (And back from hibernation I think), it's like if Python still has that client in its list of
# clients so data is sent sometimes to the first client instance (that doesn't read data anymore), sometimes to the new client, this
# makes the graph have spaces 0-values between high-value bars (test with speedtest.com). Refreshing the page multiple times "seems"
# to make it worse, but not sure, maybe Python drops clients that don't answer after a while? Or there's a max of 2 clients?
# Restarting the Python service fixes that however. So maybe periodically check if the list is still valid? Or when a new client
# connects, replace existing one if it's the same, then destroy dead futures and tasks?

if __name__ == "__main__":
    # if not is_admin():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        cprint(COLORS.RED, "You need administrator rights to run the hardware_monitor")
        sys.exit(ERROR_ADMIN)

    # Server code below
    hardware_monitor = HardwareMonitor()
    hardware_monitor.fetch_stats()
    server = Server(hardware_monitor=hardware_monitor)
