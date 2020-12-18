"""
This uses StackOverflow answer: https://stackoverflow.com/a/49909330/1046013
Same as using_openhardwaremonitor1.py, however it also uses CPUThermometer, which is a sort of fork of OpenHardwareMonitor
However, CPU Thermometer's dll seems to be 32bits (Even if website says both are included), so it won't load on
Python 64 bits. It's not needed anyways as it doesn't give any additional info after OpenHardwareMonitor
"""

import clr #package pythonnet, not clr
import os


openhardwaremonitor_hwtypes = ['Mainboard','SuperIO','CPU','RAM','GpuNvidia','GpuAti','TBalancer','Heatmaster','HDD']
cputhermometer_hwtypes = ['Mainboard','SuperIO','CPU','GpuNvidia','GpuAti','TBalancer','Heatmaster','HDD']
openhardwaremonitor_sensortypes = ['Voltage','Clock','Temperature','Load','Fan','Flow','Control','Level','Factor','Power','Data','SmallData']
cputhermometer_sensortypes = ['Voltage','Clock','Temperature','Load','Fan','Flow','Control','Level']


def initialize_openhardwaremonitor():
    file = '../lib/OpenHardwareMonitorLib.dll'
    #clr.AddReference(file)
    clr.AddReference( os.path.abspath( os.path.dirname( __file__ ) ) + R'\lib/OpenHardwareMonitorLib.dll' )

    from OpenHardwareMonitor import Hardware

    handle = Hardware.Computer()
    handle.MainboardEnabled = True
    handle.CPUEnabled = True
    handle.RAMEnabled = True
    handle.GPUEnabled = True
    handle.HDDEnabled = True
    handle.Open()
    return handle

def initialize_cputhermometer():
    file = '../lib/CPUThermometerLib.dll'
    #clr.AddReference(file)
    clr.AddReference( os.path.abspath( os.path.dirname( __file__ ) ) + R'\lib/CPUThermometerLib.dll' )

    from CPUThermometer import Hardware
    handle = Hardware.Computer()
    handle.CPUEnabled = True
    handle.Open()
    return handle

def fetch_stats(handle):
    for i in handle.Hardware:
        i.Update()
        for sensor in i.Sensors:
            parse_sensor(sensor)
        for j in i.SubHardware:
            j.Update()
            for subsensor in j.Sensors:
                parse_sensor(subsensor)


def parse_sensor(sensor):
        if sensor.Value is not None:
            if type(sensor).__module__ == 'CPUThermometer.Hardware':
                sensortypes = cputhermometer_sensortypes
                hardwaretypes = cputhermometer_hwtypes
            elif type(sensor).__module__ == 'OpenHardwareMonitor.Hardware':
                sensortypes = openhardwaremonitor_sensortypes
                hardwaretypes = openhardwaremonitor_hwtypes
            else:
                return

            if sensor.SensorType == sensortypes.index('Temperature'):
                print(u"%s %s Temperature Sensor #%i %s - %s\u00B0C" % (hardwaretypes[sensor.Hardware.HardwareType], sensor.Hardware.Name, sensor.Index, sensor.Name, sensor.Value))

if __name__ == "__main__":
    print("OpenHardwareMonitor:")
    HardwareHandle = initialize_openhardwaremonitor()
    fetch_stats(HardwareHandle)
    # print("\nCPUMonitor:")
    # CPUHandle = initialize_cputhermometer()
    # fetch_stats(CPUHandle)
