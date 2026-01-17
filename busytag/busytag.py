# SPDX-License-Identifier: MIT

from .color import parse_color_string

from typing import List
from enum import IntEnum, Enum
import serial
import os
import logging
logger = logging.getLogger(__name__)
serial_logger = logging.getLogger(f"{__name__}.serial")


class BusyTag:

    class LEDS(IntEnum):
        ALL  = 0b01111111  # 127
        LED0 = 0b00000001  # 1
        LED1 = 0b00000010  # 2
        LED2 = 0b00000100  # 4
        LED3 = 0b00001000  # 8
        LED4 = 0b00010000  # 16
        LED5 = 0b00100000  # 32
        LED6 = 0b01000000  # 64

        # Left Right Pattern
        RIGHT = 0b01111000  # 120
        LEFT  = 0b00001111  # 15

        # Running Pattern
        RUN0  = 0b10000001  # 129
        RUN1  = 0b10000010  # 130
        RUN2  = 0b10000100  # 132
        RUN3  = 0b10001000  # 136
        RUN4  = 0b10010000  # 144
        RUN5  = 0b10100000  # 160
        RUN6  = 0b11000000  # 192


    class ErrorCode(IntEnum):
        NONE = -1
        UNKNOWN_ERROR = 0
        UNKNOWN_COMMAND = 1
        INVALID_ARGUMENT = 2
        FILE_NOT_FOUND = 3
        INVALID_SIZE = 4

    class ResetReason(IntEnum):
        POWER_ON_RESET = 1
        SOFTWARE_RESETS_DIGITAL_CORE = 3
        DEEP_SLEEP_RESETS_DIGITAL_CORE = 5
        SDIO_MODULE_RESETS_DIGITAL_CORE = 6
        MAIN_WATCHDOG_0_RESETS_DIGITAL_CORE = 7
        MAIN_WATCHDOG_1_RESETS_DIGITAL_CORE = 8
        RTC_WATCHDOG_RESETS_DIGITAL_CORE = 9
        MAIN_WATCHDOG_RESETS_CPU = 11
        SOFTWARE_RESETS_CPU = 12
        RTC_WATCHDOG_RESETS_CPU = 13
        CPU0_RESETS_CPU1 = 14
        VDD_VOLTAGE_UNSTABLE = 15
        RTC_WATCHDOG_RESETS_DIGITAL_CORE_AND_TC_MODULE = 16


    def __init__(self, device, baudrate=115200, timeout=1):
        self.device = device
        self.baudrate = baudrate
        self.timeout = timeout

    def __clean_data(self, data, binary):
        if binary:
            return data

        try:
            d = data.decode('utf-8').strip()
        except UnicodeDecodeError:
            return data
        
        if 'error' in d.lower():
            if ':' in d:
                error = self.ErrorCode(int(d.split(':')[1]))
                logger.error(f"Error in output: {error.name} (Line: {d})")
            return None

        if ':' in d:
            d = d.split(':')[1]
        return d

    def __getLedsFromInt(self, led_num):
        if led_num == 127:
            return [self.LEDS.ALL]
        
        leds = []
        for i in range(0,7):
            if(led_num & (1 << i) != 0):
                leds.append(self.LEDS(2**i))
        return leds

    def write(self, data: list[bytes], binary=False):
        response = []
        try:
            
            ser = serial.Serial(self.device, baudrate=self.baudrate, timeout=self.timeout)
            for b in data:
                serial_logger.debug(f"Write data {b} to {self.device}")
                ser.write(b)
                raw_resp = ser.readlines()
                serial_logger.debug(raw_resp)
                logger.debug(raw_resp)
                response.extend(filter(None, [self.__clean_data(x, binary) for x in raw_resp]))
                #response.append(ser.readlines())
            ser.close()
        except Exception as e:
            serial_logger.exception(e)
        
        return response
    
    def showDeviceInfo(self):
        return {
            "id": self.getDeviceId(),
            "name": self.getDeviceName(),
            "manufacture": self.getManufactureName(),
            "firmware_version": self.getFirmwareVersion(),
        }

    # Get

    def getDeviceName(self):
        resp = self.write([b'AT+GDN\r\n'])
        return resp[0]

    def getManufactureName(self):
        resp = self.write([b'AT+GMN\r\n'])
        return resp[0]

    def getDeviceId(self):
        resp = self.write([b'AT+GID\r\n'])
        return resp[0]

    def getFirmwareVersion(self):
        resp = self.write([b'AT+GFV\r\n'])
        return resp[0]
        
    def getPictureList(self):
        resp = self.write([b'AT+GPL\r\n'])
        data = []
        for r in resp[:-1]:
            rs = r.split(',')
            data.append({
                "name": rs[0],
                "size": int(rs[1]),
            })
        return data

    def getFileList(self):
        resp = self.write([b'AT+GFL\r\n'])
        data = []
        for r in resp[:-1]:
            rs = r.split(',')
            data.append({
                "name": rs[0],
                "size": int(rs[2]),
                "type": rs[1],
            })
        return data

    def getLocalHostAddress(self):
        resp = self.write([b'AT+GLHA\r\n'])
        return resp[0]

    def getFreeStorageSize(self):
        resp = self.write([b'AT+GFSS\r\n'])
        return resp[0]

    def getTotalStorageSize(self):
        resp = self.write([b'AT+GTSS\r\n'])
        return resp[0]

    def getLastErrorCode(self):
        resp = self.write([b'AT+GLEC\r\n'])
        return self.ErrorCode(int(resp[0]))

    def getLastResetReasonCore0(self):
        resp = self.write([b'AT+GLRR0\r\n'])
        #return self.ResetReason(int(resp[0]))

    def getLastResetReasonCore1(self):
        resp = self.write([b'AT+GLRR1\r\n'])
        #return self.ResetReason(int(resp[0]))

    # Get/Set Config

    def getSolidColor(self):
        resp = self.write([b'AT+SC?\r\n'])
        return resp[0]

    def setSolidColor(self, color="red", scale = 1.0, leds=[LEDS.ALL], clear=True):
        c = parse_color_string(color, scale)
        # Clear ALL
        if clear: 
            buf = f"AT+SC=127,000000\r\n"
            resp = self.write([buf.encode()])
            if 'OK' not in resp:
                logger.error(resp)
        # Set Color
        buf = f"AT+SC={sum(leds)},{c[0]:02x}{c[1]:02x}{c[2]:02x}\r\n"
        resp = self.write([buf.encode()])
        if 'OK' not in resp:
            logger.error(resp)

    def getCustomPattern(self):
        resp = self.write([b'AT+CP?\r\n'])
        patterns = []
        for r in resp[:-1]:
            rs = r.split(',')
            patterns.append(str(BusyTagPattern(
                color=rs[1],
                leds=self.__getLedsFromInt(int(rs[0]))
            )))
        return patterns

    def setCustomPattern(self, patterns: List = [], repeat = 255):
        # Set Pattern
        num_pattern = len(patterns)
        buf = [f"AT+CP={num_pattern}"]
        for p in patterns:
            buf.append(f"+CP:{str(p)}\r\n")

        resp = self.write([b.encode() for b in buf])
        if 'OK' not in resp:
            logger.error(resp)

        self.playPattern(True, repeat)

    def getDisplayBrightness(self):
        resp = self.write([b'AT+DB?\r\n'])
        return resp[0]

    def setDisplayBrightness(self, brightness=100):
        if brightness < 1 or brightness > 100:
            logger.error(f"Display Brightness value must be in range 1-100")
            return

        # Set Brightness
        buf = f"AT+DB={brightness}\r\n"
        resp = self.write([buf.encode()])
        if 'OK' not in resp:
            logger.error(resp)

    def getShowAfterDrop(self):
        # AT+SAD?
        resp = self.write([b'AT+SAD?\r\n'])
        return resp[0]

    def setShowAfterDrop(self):
        # AT+SAD={0,1}
        buf = "AT+SAD=1\r\n"
        resp = self.write([buf.encode()])
        if 'OK' not in resp:
            logger.error(resp)

    def unsetShowAfterDrop(self):
        # AT+SAD={0,1}
        buf = "AT+SAD=0\r\n"
        resp = self.write([buf.encode()])
        if 'OK' not in resp:
            logger.error(resp)

    def getAllowWebFileServer(self):
        # AT+AWFS?
        resp = self.write([b'AT+AWFS?\r\n'])
        return resp[0]

    def setAllowWebFileServer(self):
        # AT+AWFS={0,1}
        buf = "AT+AWFS=1\r\n"
        resp = self.write([buf.encode()])
        if 'OK' not in resp:
            logger.error(resp)

    def unsetAllowWebFileServer(self):
        # AT+AWFS={0,1}
        buf = "AT+AWFS=0\r\n"
        resp = self.write([buf.encode()])
        if 'OK' not in resp:
            logger.error(resp)

    def getWifiConfig(self):
        # AT+WC?
        resp = self.write([b'AT+WC?\r\n'])
        return resp[0]

    def setWifiConfig(self, ssid, password):
        # AT+WC=ssid,password
        buf = f"AT+WC={ssid},{password}\r\n"
        resp = self.write([buf.encode()])
        if 'OK' not in resp:
            logger.error(resp)

    def getUsbMassStorage(self):
        # AT+UMSA?
        resp = self.write([b'AT+UMSA?\r\n'])
        return resp[0]

    def setUsbMassStorage(self):
        # AT+UMSA={0,1}
        buf = "AT+UMSA=1\r\n"
        resp = self.write([buf.encode()])
        if 'OK' not in resp:
            logger.error(resp)

    def unsetUsbMassStorage(self):
        # AT+UMSA={0,1}
        buf = "AT+UMSA=0\r\n"
        resp = self.write([buf.encode()])
        if 'OK' not in resp:
            logger.error(resp)

    def getShowingPicture(self):
        # AT+SP?
        resp = self.write([b'AT+SP?\r\n'])
        return resp[0]

    def setShowingPicture(self, filename):
        # AT+SP=filename
        buf = f"AT+SP={filename}\r\n"
        resp = self.write([buf.encode()])
        if 'OK' not in resp:
            logger.error(resp)

    def getAutoStorageScan(self):
        # AT+AASS?
        resp = self.write([b'AT+AASS?\r\n'])
        return resp[0]

    def setAutoStorageScan(self):
        # AT+AASS={0,1}
        buf = "AT+AASS=1\r\n"
        resp = self.write([buf.encode()])
        if 'OK' not in resp:
            logger.error(resp)

    def unsetAutoStorageScan(self):
        # AT+AASS={0,1}
        buf = "AT+AASS=0\r\n"
        resp = self.write([buf.encode()])
        if 'OK' not in resp:
            logger.error(resp)

    # Actions

    def playPattern(self, active: bool = True, repeat: int = 255):
        # AT+PP=allow,repeat
        # repeat 255 => infinite
        buf = f"AT+PP={1 if active else 0},{repeat}\r\n"
        resp = self.write([buf.encode()])
        if 'OK' not in resp:
            logger.error(resp)

    def getFile(self, filename, output_file=None):
        # AT+GF=filename
        buf = f"AT+GF={filename}\r\n"
        resp = self.write([buf.encode()], binary=True)
        if output_file:
            with open(output_file, "wb") as f:
                f.write(b"".join(resp[2:-1]))
        else:
            return b"".join(resp[2:-1])

    def putFile(self, filepath):
        # AT+UF=filename,size
        size = os.path.getsize(filepath)
        basename = os.path.basename(filepath)
        buf = [f"AT+UF={basename},{size}\r\n".encode()]
        with open(filepath, "rb") as f:
            buf.append(f.read())
        resp = self.write(buf)
        
        if 'OK' not in resp:
            logger.error(resp)

    def deleteFile(self, filename):
        # AT+DF=filename
        buf = f"AT+DF={filename}\r\n"
        resp = self.write([buf.encode()])
        if 'OK' not in resp:
            logger.error(resp)

    def restart(self):
        # AT+RST
        buf = b"AT+RST\r\n"
        resp = self.write([buf])
        if 'OK' not in resp:
            logger.error(resp)

    def formatDeviceStorage(self):
        # AT+FD
        buf = b"AT+FD\r\n"
        resp = self.write([buf])
        if 'OK' not in resp:
            logger.error(resp)

    def activateFileStorageScan(self):
        # AT+AFSS
        buf = b"AT+AFSS\r\n"
        resp = self.write([buf])
        if 'OK' not in resp:
            logger.error(resp)

    def factoryResetMainConfig(self):
        # AT+FRMCF
        buf = b"AT+FRMCF\r\n"
        resp = self.write([buf])
        if 'OK' not in resp:
            logger.error(resp)

    def factoryResetWifiConfig(self):
        # AT+FRWCF
        buf = b"AT+FRWCF\r\n"
        resp = self.write([buf])
        if 'OK' not in resp:
            logger.error(resp)

    def factoryResetDefaultImage(self):
        # AT+FRDI
        buf = b"AT+FRWCF\r\n"
        resp = self.write([buf])
        if 'OK' not in resp:
            logger.error(resp)

class BusyTagPattern:
    def __init__(self, leds=[BusyTag.LEDS.ALL], color="FFFFFF", scale=1.0, speed=100, delay=0):
        self.color = parse_color_string(color, scale=scale)
        self.scale = scale
        self.leds = leds
        self.speed = speed
        self.delay = delay
    
    def __str__(self):
        return f"{sum(self.leds)},{self.color[0]:02x}{self.color[1]:02x}{self.color[2]:02x},{self.speed},{self.delay}"


class BusyTagDefaultPattern(Enum):

    DEFAULT = [
        BusyTagPattern([BusyTag.LEDS.ALL], "1291AF", 1.0, 100, 0),
        BusyTagPattern([BusyTag.LEDS.ALL], "FF0000", 1.0, 100, 0),
    ]
    POLICE_1 = [
        BusyTagPattern([BusyTag.LEDS.LEFT], "FF0000", 1.0, 5, 50),
        BusyTagPattern([BusyTag.LEDS.LEFT], "000000", 1.0, 5, 50),
        BusyTagPattern([BusyTag.LEDS.RIGHT], "0000FF", 1.0, 5, 50),
        BusyTagPattern([BusyTag.LEDS.RIGHT], "000000", 1.0, 5, 50),
    ]
    POLICE_2 = [
        BusyTagPattern([BusyTag.LEDS.LEFT], "FF0000", 1.0, 3, 20),
        BusyTagPattern([BusyTag.LEDS.LEFT], "000000", 1.0, 3, 20),
        BusyTagPattern([BusyTag.LEDS.LEFT], "FF0000", 1.0, 3, 20),
        BusyTagPattern([BusyTag.LEDS.LEFT], "000000", 1.0, 3, 20),
        BusyTagPattern([BusyTag.LEDS.RIGHT], "0000FF", 1.0, 3, 20),
        BusyTagPattern([BusyTag.LEDS.RIGHT], "000000", 1.0, 5, 20),
        BusyTagPattern([BusyTag.LEDS.RIGHT], "0000FF", 1.0, 3, 20),
        BusyTagPattern([BusyTag.LEDS.RIGHT], "000000", 1.0, 5, 20),
    ]

    RED_FLASHES = [
        BusyTagPattern([BusyTag.LEDS.ALL], "FF0000", 1.0, 5, 10),
        BusyTagPattern([BusyTag.LEDS.ALL], "000000", 1.0, 5, 10),
    ]
    GREEN_FLASHES = [
        BusyTagPattern([BusyTag.LEDS.ALL], "00FF00", 1.0, 5, 10),
        BusyTagPattern([BusyTag.LEDS.ALL], "000000", 1.0, 5, 10),
    ]
    BLUE_FLASHES = [
        BusyTagPattern([BusyTag.LEDS.ALL], "0000FF", 1.0, 5, 10),
        BusyTagPattern([BusyTag.LEDS.ALL], "000000", 1.0, 5, 10),
    ]
    YELLOW_FLASHES = [
        BusyTagPattern([BusyTag.LEDS.ALL], "FFFF00", 1.0, 5, 10),
        BusyTagPattern([BusyTag.LEDS.ALL], "000000", 1.0, 5, 10),
    ]
    CYAN_FLASHES = [
        BusyTagPattern([BusyTag.LEDS.ALL], "00FFFF", 1.0, 5, 10),
        BusyTagPattern([BusyTag.LEDS.ALL], "000000", 1.0, 5, 10),
    ]
    MAGENTA_FLASHES = [
        BusyTagPattern([BusyTag.LEDS.ALL], "FF00FF", 1.0, 5, 10),
        BusyTagPattern([BusyTag.LEDS.ALL], "000000", 1.0, 5, 10),
    ]
    WHITE_FLASHES = [
        BusyTagPattern([BusyTag.LEDS.ALL], "FFFFFF", 1.0, 5, 10),
        BusyTagPattern([BusyTag.LEDS.ALL], "000000", 1.0, 5, 10),
    ]

    RED_PULSES = [
        BusyTagPattern([BusyTag.LEDS.ALL], "FF0000", 1.0, 150, 10),
        BusyTagPattern([BusyTag.LEDS.ALL], "110000", 1.0, 150, 10),
    ]
    GREEN_PULSES = [
        BusyTagPattern([BusyTag.LEDS.ALL], "00FF00", 1.0, 150, 10),
        BusyTagPattern([BusyTag.LEDS.ALL], "001100", 1.0, 150, 10),
    ]
    BLUE_PULSES = [
        BusyTagPattern([BusyTag.LEDS.ALL], "0000FF", 1.0, 150, 10),
        BusyTagPattern([BusyTag.LEDS.ALL], "000011", 1.0, 150, 10),
    ]
    YELLOW_PULSES = [
        BusyTagPattern([BusyTag.LEDS.ALL], "FFFF00", 1.0, 150, 10),
        BusyTagPattern([BusyTag.LEDS.ALL], "111100", 1.0, 150, 10),
    ]
    CYAN_PULSES = [
        BusyTagPattern([BusyTag.LEDS.ALL], "00FFFF", 1.0, 150, 10),
        BusyTagPattern([BusyTag.LEDS.ALL], "001111", 1.0, 150, 10),
    ]
    MAGENTA_PULSES = [
        BusyTagPattern([BusyTag.LEDS.ALL], "FF00FF", 1.0, 150, 10),
        BusyTagPattern([BusyTag.LEDS.ALL], "110011", 1.0, 150, 10),
    ]
    WHITE_PULSES = [
        BusyTagPattern([BusyTag.LEDS.ALL], "FFFFFF", 1.0, 150, 10),
        BusyTagPattern([BusyTag.LEDS.ALL], "111111", 1.0, 150, 10),
    ]

    RED_RUNNING = [
        BusyTagPattern([BusyTag.LEDS.RUN0], "FF0000", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN1], "FF0000", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN2], "FF0000", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN3], "FF0000", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN4], "FF0000", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN5], "FF0000", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN6], "FF0000", 1.0, 10, 0),
    ]
    GREEN_RUNNING = [
        BusyTagPattern([BusyTag.LEDS.RUN0], "00FF00", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN1], "00FF00", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN2], "00FF00", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN3], "00FF00", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN4], "00FF00", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN5], "00FF00", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN6], "00FF00", 1.0, 10, 0),
    ]
    BLUE_RUNNING = [
        BusyTagPattern([BusyTag.LEDS.RUN0], "0000FF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN1], "0000FF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN2], "0000FF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN3], "0000FF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN4], "0000FF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN5], "0000FF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN6], "0000FF", 1.0, 10, 0),
    ]
    YELLOW_RUNNING = [
        BusyTagPattern([BusyTag.LEDS.RUN0], "FFFF00", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN1], "FFFF00", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN2], "FFFF00", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN3], "FFFF00", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN4], "FFFF00", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN5], "FFFF00", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN6], "FFFF00", 1.0, 10, 0),
    ]
    CYAN_RUNNING = [
        BusyTagPattern([BusyTag.LEDS.RUN0], "00FFFF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN1], "00FFFF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN2], "00FFFF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN3], "00FFFF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN4], "00FFFF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN5], "00FFFF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN6], "00FFFF", 1.0, 10, 0),
    ]
    MAGENTA_RUNNING = [
        BusyTagPattern([BusyTag.LEDS.RUN0], "FF00FF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN1], "FF00FF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN2], "FF00FF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN3], "FF00FF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN4], "FF00FF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN5], "FF00FF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN6], "FF00FF", 1.0, 10, 0),
    ]
    WHITE_RUNNING = [
        BusyTagPattern([BusyTag.LEDS.RUN0], "FFFFFF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN1], "FFFFFF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN2], "FFFFFF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN3], "FFFFFF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN4], "FFFFFF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN5], "FFFFFF", 1.0, 10, 0),
        BusyTagPattern([BusyTag.LEDS.RUN6], "FFFFFF", 1.0, 10, 0),
    ]

