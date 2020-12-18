from collections import namedtuple

SERIAL_PORT = 'COM4'
SERIAL_BAUD_RATE = '115200'
SERIAL_RTSCTS = False

ERROR_SERIAL = 1
ERROR_ADMIN = 2

HARDWARE_TYPES = [
    "Motherboard",
    "SuperIO",
    "Cpu",
    "Memory",
    "GpuNvidia",
    "GpuAmd",
    "Storage",
    "Network",
    "Cooler",
]

Sensor = namedtuple("Sensor", "name unit")
SENSORS = [
    Sensor(name="Voltage", unit="V"),
    Sensor(name="Clock", unit="MHz"),
    Sensor(name="Temperature", unit="\u00B0C"),
    Sensor(name="Load", unit="%"),
    Sensor(name="Frequency", unit="Hz"),
    Sensor(name="Fan", unit="RPM"),
    Sensor(name="Flow", unit="L/h"),
    Sensor(name="Control", unit="%"),
    Sensor(name="Level", unit="%"),
    Sensor(name="Factor", unit="1"),
    Sensor(name="Power", unit="W"),
    Sensor(name="Data", unit="GB = 2^30 Bytes"),
    Sensor(name="SmallData", unit="MB = 2^20 Bytes"),
    Sensor(name="Throughput", unit="B/s"),
]