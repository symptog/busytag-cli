from enum import IntEnum
import serial
import os
import logging
logger = logging.getLogger(__name__)
serial_logger = logging.getLogger(f"{__name__}.serial")

from .color import parse_color_string

class BusyTag:

    class LEDS(IntEnum):
        ALL  = 0b01111111
        LED0 = 0b00000001
        LED1 = 0b00000010
        LED2 = 0b00000100
        LED3 = 0b00001000
        LED4 = 0b00010000
        LED5 = 0b00100000
        LED6 = 0b01000000
    
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
                response.extend([self.__clean_data(x, binary) for x in raw_resp])
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

    def setCustomPattern(self, patterns=[]):
        # Set Pattern
        num_pattern = len(patterns)
        buf = [f"AT+CP={num_pattern}"]
        for p in patterns:
            buf.append(f"+CP={p}\r\n")

        resp = self.write([b.encode() for b in buf])
        if 'OK' not in resp:
            logger.error(resp)

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
    def __init__(self, color, scale=1.0, leds=[BusyTag.LEDS.ALL], speed=100, delay=0):
        self.color = parse_color_string(color)
        self.scale = scale
        self.leds = leds
        self.speed = speed
        self.delay = delay
    
    def __str__(self):
        return f"{sum(self.leds)},{self.color[0]:02x}{self.color[1]:02x}{self.color[2]:02x},{self.speed},{self.delay}"
