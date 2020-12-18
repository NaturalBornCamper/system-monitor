# -*- coding: utf-8 -*-

import wmi

#
# def avg(value_list):
#     num = 0
#     length = len(value_list)
#     for val in value_list:
#         num += val
#     return num / length
#
# w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
# sensors = w.Sensor()
# cpu_temps = []
# gpu_temp = 0
# for sensor in sensors:
#     if sensor.SensorType == u'Temperature' and not 'GPU' in sensor.Name:
#         cpu_temps += [float(sensor.Value)]
#     elif sensor.SensorType == u'Temperature' and 'GPU' in sensor.Name:
#         gpu_temp = sensor.Value
# print("Avg CPU: {}".format(avg(cpu_temps)))
# print("GPU: {}".format(gpu_temp))


# import wmi
# c = wmi.WMI()
# for s in c.Win32_Service(StartMode="Auto", State="Stopped"):
#     if raw_input("Restart %s? " % s.Caption).upper() == "Y":
#         s.StartService()

c = wmi.WMI()

# for s in c.MSAcpi_ThermalZoneTemperature.methods.keys():
#     print(s)

print("="*40, "WMI Win32_TemperatureProbe", "="*40)
for s in c.Win32_TemperatureProbe():
    print(f"Name: {s.Name}")
    print(f"Caption: {s.Caption}")
    print(f"Description: {s.Description}")

print("="*40, "WMI CIM_TemperatureSensor", "="*40)
for s in c.CIM_TemperatureSensor():
    print(f"Name: {s.Name}")
    print(f"Caption: {s.Caption}")
    print(f"Description: {s.Description}")


print("="*40, "WMI Win32_OperatingSystem", "="*40)
for os in c.Win32_OperatingSystem():
  print(os.Caption)


# Needs administrator rights
# One value on Gigabyte: TZ00_0 28 Celcius
print("="*40, "WMI MSAcpi_ThermalZoneTemperature", "="*40)
c = wmi.WMI(namespace="WMI")
for s in c.MSAcpi_ThermalZoneTemperature():
    # print(s)
    print("{}: {}°C".format(s.InstanceName, s.CurrentTemperature/10 - 273))

# Supposed to have "CurrentReading" in Stackoverflow but don't have it on laptop OR gigabyte
print("="*40, "WMI Win32_TemperatureProbe", "="*40)
c = wmi.WMI()
for s in c.Win32_TemperatureProbe():
    print(s)
    print("{} MinReadable: {}°C, MaxReadable: {}°C".format(s.DeviceID, s.MinReadable/10 - 273, s.MaxReadable/10 - 273))



# wql = "SELECT * FROM MSAcpi_ThermalZoneTemperature"
# for disk in c.query(wql):
#     print(disk.CurrentTemperature)
# strComputer = "."
# Set objWMIService = GetObject("winmgmts:\\" & strComputer & "\root\WMI")
# Set colItems = objWMIService.ExecQuery( _
#     "SELECT * FROM MSAcpi_ThermalZoneTemperature",,48)
# For Each objItem in colItems
#     Wscript.Echo "-----------------------------------"
#     Wscript.Echo "MSAcpi_ThermalZoneTemperature instance"
#     Wscript.Echo "-----------------------------------"
#     Wscript.Echo "CurrentTemperature: " & objItem.CurrentTemperature
# Next

# c = wmi.WMI(namespace="WMI")
# for s in c.MSAcpi_ThermalZoneTemperature():
#     pass
    # print(s)
    # print(f"Name: {s.Name}")
    # print(f"Caption: {s.Caption}")
    # print(f"Description: {s.Description}")
    # print(f"CurrentTemperature: {s.CurrentTemperature}")

