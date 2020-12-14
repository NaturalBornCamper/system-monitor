"""
From this url, gives zeros everywhere though
https://stackoverflow.com/a/58924992/1046013
"""

import ctypes
import ctypes.wintypes as wintypes
from ctypes import windll


LPDWORD = ctypes.POINTER(wintypes.DWORD)
LPOVERLAPPED = wintypes.LPVOID
LPSECURITY_ATTRIBUTES = wintypes.LPVOID

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
GENERIC_EXECUTE = 0x20000000
GENERIC_ALL = 0x10000000

FILE_SHARE_WRITE=0x00000004
ZERO=0x00000000

CREATE_NEW = 1
CREATE_ALWAYS = 2
OPEN_EXISTING = 3
OPEN_ALWAYS = 4
TRUNCATE_EXISTING = 5

FILE_ATTRIBUTE_NORMAL = 0x00000080

INVALID_HANDLE_VALUE = -1
FILE_DEVICE_UNKNOWN=0x00000022
METHOD_BUFFERED=0
FUNC=0x900
FILE_WRITE_ACCESS=0x002

NULL = 0
FALSE = wintypes.BOOL(0)
TRUE = wintypes.BOOL(1)


def CTL_CODE(DeviceType, Function, Method, Access): return (DeviceType << 16) | (Access << 14) | (Function <<2) | Method




def _CreateFile(filename, access, mode, creation, flags):
    """See: CreateFile function http://msdn.microsoft.com/en-us/library/windows/desktop/aa363858(v=vs.85).asp """
    CreateFile_Fn = windll.kernel32.CreateFileW
    CreateFile_Fn.argtypes = [
            wintypes.LPWSTR,                    # _In_          LPCTSTR lpFileName
            wintypes.DWORD,                     # _In_          DWORD dwDesiredAccess
            wintypes.DWORD,                     # _In_          DWORD dwShareMode
            LPSECURITY_ATTRIBUTES,              # _In_opt_      LPSECURITY_ATTRIBUTES lpSecurityAttributes
            wintypes.DWORD,                     # _In_          DWORD dwCreationDisposition
            wintypes.DWORD,                     # _In_          DWORD dwFlagsAndAttributes
            wintypes.HANDLE]                    # _In_opt_      HANDLE hTemplateFile
    CreateFile_Fn.restype = wintypes.HANDLE

    return wintypes.HANDLE(CreateFile_Fn(filename,
                         access,
                         mode,
                         NULL,
                         creation,
                         flags,
                         NULL))


handle=_CreateFile('\\\\.\\AdvLmDev',GENERIC_WRITE,FILE_SHARE_WRITE,OPEN_EXISTING,ZERO)

def _DeviceIoControl(devhandle, ioctl, inbuf, inbufsiz, outbuf, outbufsiz):
    """See: DeviceIoControl function
http://msdn.microsoft.com/en-us/library/aa363216(v=vs.85).aspx
"""
    DeviceIoControl_Fn = windll.kernel32.DeviceIoControl
    DeviceIoControl_Fn.argtypes = [
            wintypes.HANDLE,                    # _In_          HANDLE hDevice
            wintypes.DWORD,                     # _In_          DWORD dwIoControlCode
            wintypes.LPVOID,                    # _In_opt_      LPVOID lpInBuffer
            wintypes.DWORD,                     # _In_          DWORD nInBufferSize
            wintypes.LPVOID,                    # _Out_opt_     LPVOID lpOutBuffer
            wintypes.DWORD,                     # _In_          DWORD nOutBufferSize
            LPDWORD,                            # _Out_opt_     LPDWORD lpBytesReturned
            LPOVERLAPPED]                       # _Inout_opt_   LPOVERLAPPED lpOverlapped
    DeviceIoControl_Fn.restype = wintypes.BOOL

    # allocate a DWORD, and take its reference
    dwBytesReturned = wintypes.DWORD(0)
    lpBytesReturned = ctypes.byref(dwBytesReturned)

    status = DeviceIoControl_Fn(devhandle,
                  ioctl,
                  inbuf,
                  inbufsiz,
                  outbuf,
                  outbufsiz,
                  lpBytesReturned,
                  NULL)

    return status, dwBytesReturned

class OUTPUT_temp(ctypes.Structure):
        """See: http://msdn.microsoft.com/en-us/library/aa363972(v=vs.85).aspx"""
        _fields_ = [
                ('Board Temp', wintypes.DWORD),
                ('CPU Temp', wintypes.DWORD),
                ('Board Temp2', wintypes.DWORD),
                ('temp4', wintypes.DWORD),
                ('temp5', wintypes.DWORD)
                ]

class OUTPUT_volt(ctypes.Structure):
        """See: http://msdn.microsoft.com/en-us/library/aa363972(v=vs.85).aspx"""
        _fields_ = [
                ('VCore', wintypes.DWORD),
                ('V(in2)', wintypes.DWORD),
                ('3.3V', wintypes.DWORD),
                ('5.0V', wintypes.DWORD),
                ('temp5', wintypes.DWORD)
                ]

def get_temperature():
    FUNC=0x900
    outDict={}

    ioclt=CTL_CODE(FILE_DEVICE_UNKNOWN, FUNC, METHOD_BUFFERED, FILE_WRITE_ACCESS)

    handle=_CreateFile('\\\\.\\AdvLmDev',GENERIC_WRITE,FILE_SHARE_WRITE,OPEN_EXISTING,ZERO)

    win_list = OUTPUT_temp()
    p_win_list = ctypes.pointer(win_list)
    SIZE=ctypes.sizeof(OUTPUT_temp)


    status, output = _DeviceIoControl(handle, ioclt , NULL, ZERO, p_win_list, SIZE)


    for field, typ in win_list._fields_:
                #print ('%s=%d' % (field, getattr(disk_geometry, field)))
                outDict[field]=getattr(win_list,field)
    return outDict

def get_voltages():
    FUNC=0x901
    outDict={}

    ioclt=CTL_CODE(FILE_DEVICE_UNKNOWN, FUNC, METHOD_BUFFERED, FILE_WRITE_ACCESS)

    handle=_CreateFile('\\\\.\\AdvLmDev',GENERIC_WRITE,FILE_SHARE_WRITE,OPEN_EXISTING,ZERO)

    win_list = OUTPUT_volt()
    p_win_list = ctypes.pointer(win_list)
    SIZE=ctypes.sizeof(OUTPUT_volt)


    status, output = _DeviceIoControl(handle, ioclt , NULL, ZERO, p_win_list, SIZE)


    for field, typ in win_list._fields_:
                #print ('%s=%d' % (field, getattr(disk_geometry, field)))
                outDict[field]=getattr(win_list,field)
    return outDict


print(get_temperature())
print(get_voltages())
