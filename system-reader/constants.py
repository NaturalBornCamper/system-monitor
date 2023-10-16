from collections import namedtuple
import enum

DEBUG = False

# WEBSOCKET_BROADCAST_DELAY_SECONDS = 2
WEBSOCKET_BROADCAST_DELAY_SECONDS = 0.5

SOCKET_PORT = 2346
SOCKET_MAX_CONNECTION = 1

SERIAL_PORT = 'COM4'
SERIAL_BAUD_RATE = '115200'
SERIAL_RTSCTS = False

ERROR_SERIAL = 1
ERROR_ADMIN = 2

# If updating LibreHardwareMonitor dll files, make sure these values are still the same, taken from
# https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/blob/master/LibreHardwareMonitorLib/Hardware/HardwareType.cs
HARDWARE_TYPES = [
    "Motherboard",
    "SuperIO",
    "Cpu",
    "Memory",
    "GpuNvidia",
    "GpuAmd",
    "GpuIntel",
    "Storage",
    "Network",
    "Cooler",
    "EmbeddedController",
    "Psu",
    "Battery",
]

Sensor = namedtuple("Sensor", "name unit")
# If updating LibreHardwareMonitor dll files, make sure these values are still the same, taken from
# https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/blob/master/LibreHardwareMonitorLib/Hardware/ISensor.cs
SENSOR_TYPES = [
    Sensor(name="Voltage", unit="V"),
    Sensor(name="Current", unit="A"),
    Sensor(name="Power", unit="W"),
    Sensor(name="Clock", unit="MHz"),
    Sensor(name="Temperature", unit="\u00B0C"),
    Sensor(name="Load", unit="%"),
    Sensor(name="Frequency", unit="Hz"),
    Sensor(name="Fan", unit="RPM"),
    Sensor(name="Flow", unit="L/h"),
    Sensor(name="Control", unit="%"),
    Sensor(name="Level", unit="%"),
    Sensor(name="Factor", unit="1"),
    Sensor(name="Data", unit="GB = 2^30 Bytes"),
    Sensor(name="SmallData", unit="MB = 2^20 Bytes"),
    Sensor(name="Throughput", unit="B/s"),
    Sensor(name="TimeSpan", unit="Seconds"),
    Sensor(name="Energy", unit="milliwatt-hour (mWh)"),
    Sensor(name="Noise", unit="Decibels (dBA)"),
]

# TODO Should it be per-case? 0.1s is nothing when max delay is 10s, but it's a lot if max delay is 0.4s. Maybe use percentage instead?
UPDATE_THRESHOLD = 0.1


class Sensor:
    HARDWARE = 'hardware'
    SUB_HARDWARE = 'sub_hardware'
    SENSOR = 'sensor'
    DELAY = 'delay'
    VALUE = 'value'
    UNIT = "unit"


class Actions(enum.IntEnum):
    SET_SENSORS, STOP_BROADCAST, CHANGE_DELAY = range(3)
