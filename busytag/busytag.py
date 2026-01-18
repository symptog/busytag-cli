# SPDX-License-Identifier: MIT

from .color import parse_color_string

from typing import List, Dict
from enum import IntEnum, Enum
import serial
import os
import logging
logger = logging.getLogger(__name__)
serial_logger = logging.getLogger(f"{__name__}.serial")


class BusyTag:
    """Main class for interacting with BusyTag devices via serial communication.
    
    This class provides methods to control various aspects of the BusyTag device,
    including LED patterns, device configuration, file management, and more.
    """

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


    def __init__(self, device, baudrate=115200, timeout=1, keep_serial: bool = True):
        """Initialize the BusyTag device connection.
        
        This constructor sets up the serial communication parameters for the BusyTag device.
        The actual serial connection is established when data is written.
        
        Args:
            device: String representing the serial device path (e.g., '/dev/ttyUSB0')
            baudrate: Integer specifying the baud rate for serial communication (default: 115200)
            timeout: Integer specifying the timeout in seconds for serial operations (default: 1)
            keep_serial: Boolean flag indicating whether to keep the serial connection open
                       after each write operation (default: True)
        
        Attributes:
            device: Serial device path
            baudrate: Baud rate for communication
            timeout: Timeout value for operations
            keep_serial: Flag to control serial connection lifecycle
            ser: Serial connection object (initialized as None)
        """
        self.device = device
        self.baudrate = baudrate
        self.timeout = timeout
        self.keep_serial = keep_serial
        self.ser = None

    def __clean_data(self, data: bytes, binary: bool) -> str | bytes | None: 
        """Clean and parse serial data from the BusyTag device.
        
        This internal method processes raw serial data, handling both binary and text responses.
        For text data, it decodes UTF-8, strips whitespace, and extracts the value after ':'
        if present. It also detects and logs error messages from the device.
        
        Args:
            data: Raw bytes received from the serial device
            binary: Boolean flag indicating if the data should be treated as binary
                    (no decoding or processing)
        
        Returns:
            For binary mode: Returns the raw data unchanged
            For text mode: Returns the decoded and cleaned string, or None if an error
            was detected
            
        Error Handling:
            - UnicodeDecodeError: Returns raw data if decoding fails
            - Error messages: Logs the error code and returns None
        """
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

    def __getLedsFromInt(self, led_num) -> List[LEDS]:
        """Convert LED bitmask to list of LED enums.
        
        This internal method converts an integer bitmask representing LED positions
        into a list of LED enum values. Special handling for value 127 (ALL LEDs).
        
        Args:
            led_num: Integer bitmask representing LED positions
            
        Returns:
            List of LED enum values corresponding to the bitmask
            
        Example
            >>> self.__getLedsFromInt(127)
            [<LED.ALL: 127>]
            >>> self.__getLedsFromInt(3)  # LED0 + LED1
            [<LED.LED0: 1>, <LED.LED1: 2>]
        """
        if led_num == 127:
            return [self.LEDS.ALL]
        
        leds = []
        for i in range(0,7):
            if(led_num & (1 << i) != 0):
                leds.append(self.LEDS(2**i))
        return leds

    def write(self, data: list[bytes], binary=False) -> List[str] | List[bytes]:
        """Write data to the BusyTag device and read responses.
        
        This method handles serial communication with the BusyTag device, sending
        commands and reading responses. It manages the serial connection lifecycle
        based on the keep_serial flag.
        
        Args:
            data: List of byte strings to write to the device
            binary: Boolean flag indicating if data should be treated as binary
                   (default: False)
        
        Returns:
            List of responses from the device, cleaned and parsed according to
            the binary flag
            
        Note:
            - If keep_serial is False, the serial connection is closed after
              writing
            - Error responses are logged and filtered out
            - Binary mode returns raw data without decoding
        """
        response: list[str] | list[bytes] = []
        try:
            if self.ser:
                if not self.ser.is_open:
                    self.ser.open()
            else:
                self.ser = serial.Serial(self.device, baudrate=self.baudrate, timeout=self.timeout)

            for b in data:
                serial_logger.debug(f"Write data {b} to {self.device}")
                self.ser.write(b)
                raw_resp: list[bytes] = self.ser.readlines()
                serial_logger.debug(raw_resp)
                logger.debug(raw_resp)
                response.extend(filter(None, [self.__clean_data(x, binary) for x in raw_resp]))
                #response.append(ser.readlines())
            if not self.keep_serial:
                self.ser.close()
                self.ser = None
        except Exception as e:
            serial_logger.exception(e)
        
        return response
    
    def showDeviceInfo(self) -> Dict[str, str]:
        """Get comprehensive information about the BusyTag device.
        
        Returns a dictionary containing device identification and firmware information.
        
        Returns:
            Dictionary with keys:
            - id: Device ID string
            - name: Device name string
            - manufacture: Manufacturer name string
            - firmware_version: Firmware version string
            
        Example:
            {
                "id": "BT123456",
                "name": "BusyTag",
                "manufacture": "BusyTag Inc.",
                "firmware_version": "1.0.0"
            }
        """
        return {
            "id": self.getDeviceId(),
            "name": self.getDeviceName(),
            "manufacture": self.getManufactureName(),
            "firmware_version": self.getFirmwareVersion(),
        }

    # Get

    def getDeviceName(self) -> str:
        """Get the device name from the BusyTag.
        
        Returns:
            String containing the device name
            
        Example:
            "BusyTag"
        """
        resp: list[str] = self.write([b'AT+GDN\r\n']) # ty: ignore[invalid-assignment]
        return resp[0]

    def getManufactureName(self) -> str:
        """Get the manufacturer name from the BusyTag.
        
        Returns:
            String containing the manufacturer name
            
        Example:
            "BusyTag Inc."
        """
        resp: list[str] = self.write([b'AT+GMN\r\n']) # ty: ignore[invalid-assignment]
        return resp[0]

    def getDeviceId(self) -> str:
        """Get the unique device ID from the BusyTag.
        
        Returns:
            String containing the unique device identifier
            
        Example:
            "BT123456"
        """
        resp: list[str] = self.write([b'AT+GID\r\n']) # ty: ignore[invalid-assignment]
        return resp[0]

    def getFirmwareVersion(self) -> str:
        """Get the firmware version from the BusyTag.
        
        Returns:
            String containing the firmware version
            
        Example:
            "1.0.0"
        """
        resp: list[str] = self.write([b'AT+GFV\r\n']) # ty: ignore[invalid-assignment]
        return resp[0]
        
    def getPictureList(self) -> List[Dict]:
        """Get a list of pictures stored on the BusyTag device.
        
        Returns:
            List of dictionaries, each containing:
            - name: Picture filename
            - size: Picture file size in bytes
            
        Example:
            [
                {"name": "pic1.jpg", "size": 102400},
                {"name": "pic2.jpg", "size": 204800}
            ]
        """
        resp: list[str] = self.write([b'AT+GPL\r\n']) # ty: ignore[invalid-assignment]
        data = []
        for r in resp[:-1]:
            rs = r.split(",")
            data.append({
                "name": rs[0],
                "size": int(rs[1]),
            })
        return data

    def getFileList(self) -> List[Dict]:
        """Get a list of files stored on the BusyTag device.
        
        Returns:
            List of dictionaries, each containing:
            - name: File name
            - type: File type
            - size: File size in bytes
            
        Example:
            [
                {"name": "file1.txt", "type": "file", "size": 1024},
                {"name": "file2.bin", "type": "file", "size": 2048}
            ]
        """
        resp: list[str] = self.write([b'AT+GFL\r\n']) # ty: ignore[invalid-assignment]
        data = []
        for r in resp[:-1]:
            rs = r.split(",")
            data.append({
                "name": rs[0],
                "size": int(rs[2]),
                "type": rs[1],
            })
        return data

    def getLocalHostAddress(self) -> str:
        """Get the local host address (IP) of the BusyTag device.
        
        Returns:
            String containing the IP address
            
        Example:
            "192.168.1.100"
        """
        resp: list[str] = self.write([b'AT+GLHA\r\n']) # ty: ignore[invalid-assignment]
        return resp[0]

    def getFreeStorageSize(self) -> str:
        """Get the free storage size on the BusyTag device.
        
        Returns:
            String containing the free storage size in bytes
            
        Example:
            "104857600" (100 MB)
        """
        resp: list[str] = self.write([b'AT+GFSS\r\n']) # ty: ignore[invalid-assignment]
        return resp[0]

    def getTotalStorageSize(self) -> str:
        """Get the total storage size on the BusyTag device.
        
        Returns:
            String containing the total storage size in bytes
            
        Example:
            "209715200" (200 MB)
        """
        resp: list[str] = self.write([b'AT+GTSS\r\n']) # ty: ignore[invalid-assignment]
        return resp[0]

    def getLastErrorCode(self):
        """Get the last error code from the BusyTag device.
        
        Returns:
            ErrorCode enum value representing the last error
            
        Example:
            ErrorCode.NONE
        """
        resp: list[str] = self.write([b'AT+GLEC\r\n']) # ty: ignore[invalid-assignment]
        return self.ErrorCode(int(resp[0]))

    def getLastResetReasonCore0(self):
        """Get the last reset reason for Core 0 of the BusyTag device.
        
        Returns:
            ResetReason enum value representing the reset reason
            
        Note:
            This method is currently commented out in the implementation.
        """
        resp: list[str] = self.write([b'AT+GLRR0\r\n']) # ty: ignore[invalid-assignment]
        #return self.ResetReason(int(resp[0]))

    def getLastResetReasonCore1(self):
        """Get the last reset reason for Core 1 of the BusyTag device.
        
        Returns:
            ResetReason enum value representing the reset reason
            
        Note:
            This method is currently commented out in the implementation.
        """
        resp: list[str] = self.write([b'AT+GLRR1\r\n']) # ty: ignore[invalid-assignment]
        #return self.ResetReason(int(resp[0]))

    # Get/Set Config

    def getSolidColor(self) -> str:
        """Get the current solid color configuration from the BusyTag device.
        
        Returns:
            String containing the solid color information
            
        Example:
            "127,FF0000" (all LEDs red)
        """
        resp: list[str] = self.write([b'AT+SC?\r\n']) # ty: ignore[invalid-assignment]
        return resp[0]

    def setSolidColor(self, color: str = "red", scale: float = 1.0, leds: List[LEDS] = [LEDS.ALL], clear: bool = True) -> None:
        """Set a solid color on the BusyTag device.
        
        This method configures the BusyTag to display a solid color on specified LEDs.
        Optionally clears all LEDs to black before setting the new color.
        
        Args:
            color: String or tuple representing the color (default: "red")
            scale: Float value to scale the color brightness (default: 1.0)
            leds: List of LED enums to apply the color to (default: [LEDS.ALL])
            clear: Boolean flag to clear all LEDs before setting color (default: True)
            
        Example:
            >>> tag.setSolidColor("blue", leds=[BusyTag.LEDS.LEFT])
            # Sets left LEDs to blue
        """
        c = parse_color_string(color, scale)
        # Clear ALL
        if clear:
            buf = "AT+SC=127,000000\r\n"
            resp: list[str] = self.write([buf.encode()]) # ty: ignore[invalid-assignment]
            if 'OK' not in resp:
                logger.error(resp)
        # Set Color
        buf = f"AT+SC={sum(leds)},{c[0]:02x}{c[1]:02x}{c[2]:02x}\r\n"
        resp: list[str] = self.write([buf.encode()]) # ty: ignore[invalid-assignment]
        if 'OK' not in resp:
            logger.error(resp)

    def getCustomPattern(self) -> List['BusyTagPattern']:
        """Get the current custom pattern configuration from the BusyTag device.
        
        Returns:
            List of BusyTagPattern objects representing the current custom pattern
            
        Example:
            [<BusyTagPattern object>, <BusyTagPattern object>]
        """
        resp: list[str] = self.write([b'AT+CP?\r\n']) # ty: ignore[invalid-assignment]
        patterns = []
        for r in resp[:-1]:
            rs = r.split(',') 
            patterns.append(str(BusyTagPattern(
                color=str(rs[1]),
                leds=self.__getLedsFromInt(int(rs[0])),
                speed=int(rs[2]),
                delay=int(rs[3])
            )))
        return patterns

    def setCustomPattern(self, patterns: List = ['BusyTagPattern'], repeat = 255, active: bool = True) -> None:
        """Set a custom pattern on the BusyTag device.
        
        This method configures the BusyTag to display a sequence of patterns,
        which can be repeated a specified number of times.
        
        Args:
            patterns: List of BusyTagPattern objects to display (default: [])
            repeat: Integer specifying how many times to repeat the pattern (default: 255)
                   Use 255 for infinite repetition
            
        Example:
            >>> patterns = [BusyTagPattern(color="red"), BusyTagPattern(color="blue")]
            >>> tag.setCustomPattern(patterns, repeat=5)
            # Plays red then blue, 5 times
        """
        # Set Pattern
        num_pattern = len(patterns)
        buf = [f"AT+CP={num_pattern}"]
        for p in patterns:
            buf.append(f"+CP:{str(p)}\r\n")

        resp: list[str] = self.write([b.encode() for b in buf]) # ty: ignore[invalid-assignment]
        if 'OK' not in resp:
            logger.error(resp)

        self.playPattern(active=active, repeat=repeat)

    def getDisplayBrightness(self) -> str:
        """Get the current display brightness setting from the BusyTag device.
        
        Returns:
            String containing the brightness value (0-100)
            
        Example:
            "100"
        """
        resp: list[str] = self.write([b'AT+DB?\r\n']) # ty: ignore[invalid-assignment]
        return resp[0]

    def setDisplayBrightness(self, brightness: int = 100) -> None:
        """Set the display brightness on the BusyTag device.
        
        This method configures the brightness level of the BusyTag's display.
        The brightness value must be between 1 and 100.
        
        Args:
            brightness: Integer value specifying the brightness level (default: 100)
                      Must be in range 1-100
            
        Returns:
            None
            
        Example:
            >>> tag.setDisplayBrightness(75)
            # Sets display brightness to 75%
        """
        if brightness < 1 or brightness > 100:
            logger.error("Display Brightness value must be in range 1-100")
            return

        # Set Brightness
        buf = f"AT+DB={brightness}\r\n"
        resp: list[str] = self.write([buf.encode()]) # ty: ignore[invalid-assignment]
        if 'OK' not in resp:
            logger.error(resp)

    def getShowAfterDrop(self) -> str:
        """Get the current "Show After Drop" configuration from the BusyTag device.
        
        This setting determines whether the BusyTag displays patterns after being
        dropped or moved.
        
        Returns:
            String containing the configuration value (0 or 1)
            
        Example:
            "1" (enabled)
        """
        # AT+SAD?
        resp: list[str] = self.write([b'AT+SAD?\r\n']) # ty: ignore[invalid-assignment]
        return resp[0]

    def setShowAfterDrop(self) -> None:
        """Enable the "Show After Drop" feature on the BusyTag device.
        
        This method enables automatic pattern display when the device is dropped
        or moved.
        
        Returns:
            None
            
        Example:
            >>> tag.setShowAfterDrop()
            # Enables automatic display after drop
        """
        # AT+SAD={0,1}
        buf = "AT+SAD=1\r\n"
        resp: list[str] = self.write([buf.encode()]) # ty: ignore[invalid-assignment]
        if 'OK' not in resp:
            logger.error(resp)

    def unsetShowAfterDrop(self) -> None:
        """Disable the "Show After Drop" feature on the BusyTag device.
        
        This method disables automatic pattern display when the device is dropped
        or moved.
        
        Returns:
            None
            
        Example:
            >>> tag.unsetShowAfterDrop()
            # Disables automatic display after drop
        """
        # AT+SAD={0,1}
        buf = "AT+SAD=0\r\n"
        resp: list[str] = self.write([buf.encode()]) # ty: ignore[invalid-assignment]
        if 'OK' not in resp:
            logger.error(resp)

    def getAllowWebFileServer(self) -> str:
        """Get the current "Allow Web File Server" configuration from the BusyTag device.
        
        This setting determines whether the BusyTag allows file access via web server.
        
        Returns:
            String containing the configuration value (0 or 1)
            
        Example:
            "1" (enabled)
        """
        # AT+AWFS?
        resp: list[str] = self.write([b'AT+AWFS?\r\n']) # ty: ignore[invalid-assignment]
        return resp[0]

    def setAllowWebFileServer(self) -> None:
        """Enable the "Allow Web File Server" feature on the BusyTag device.
        
        This method enables file access via web server on the BusyTag device.
        
        Returns:
            None
            
        Example:
            >>> tag.setAllowWebFileServer()
            # Enables web file server access
        """
        # AT+AWFS={0,1}
        buf = "AT+AWFS=1\r\n"
        resp: list[str] = self.write([buf.encode()]) # ty: ignore[invalid-assignment]
        if 'OK' not in resp:
            logger.error(resp)

    def unsetAllowWebFileServer(self) -> None:
        """Disable the "Allow Web File Server" feature on the BusyTag device.
        
        This method disables file access via web server on the BusyTag device.
        
        Returns:
            None
            
        Example:
            >>> tag.unsetAllowWebFileServer()
            # Disables web file server access
        """
        # AT+AWFS={0,1}
        buf = "AT+AWFS=0\r\n"
        resp: list[str] = self.write([buf.encode()]) # ty: ignore[invalid-assignment]
        if 'OK' not in resp:
            logger.error(resp)

    def getWifiConfig(self) -> str:
        """Get the current WiFi configuration from the BusyTag device.
        
        This method retrieves the WiFi SSID and password configuration stored
        on the BusyTag device.
        
        Returns:
            String containing the WiFi configuration in format "ssid,password"
            
        Example:
            "MyWiFi,mysecurepassword123"
        """
        # AT+WC?
        resp: list[str] = self.write([b'AT+WC?\r\n']) # ty: ignore[invalid-assignment]
        return resp[0]

    def setWifiConfig(self, ssid: str, password: str) -> None:
        """Set the WiFi configuration on the BusyTag device.
        
        This method configures the WiFi SSID and password for the BusyTag device,
        allowing it to connect to a WiFi network.
        
        Args:
            ssid: String containing the WiFi network SSID (name)
            password: String containing the WiFi network password
            
        Returns:
            None
            
        Example:
            >>> tag.setWifiConfig("MyWiFi", "mysecurepassword123")
            # Configures the device to connect to "MyWiFi" network
        """
        # AT+WC=ssid,password
        buf = f"AT+WC={ssid},{password}\r\n"
        resp: list[str] = self.write([buf.encode()]) # ty: ignore[invalid-assignment]
        if 'OK' not in resp:
            logger.error(resp)

    def getUsbMassStorage(self) -> str:
        """Get the current USB mass storage configuration from the BusyTag device.
        
        This method retrieves the USB mass storage setting, which determines whether
        the BusyTag appears as a USB storage device when connected to a computer.
        
        Returns:
            String containing the configuration value (0 or 1)
            
        Example:
            "1" (enabled)
        """
        # AT+UMSA?
        resp: list[str] = self.write([b'AT+UMSA?\r\n']) # ty: ignore[invalid-assignment]
        return resp[0]

    def setUsbMassStorage(self) -> None:
        """Enable USB mass storage mode on the BusyTag device.
        
        This method enables USB mass storage mode, allowing the BusyTag to appear
        as a USB storage device when connected to a computer. This enables file
        transfer via standard file explorer.
        
        Returns:
            None
            
        Example:
            >>> tag.setUsbMassStorage()
            # Enables USB mass storage mode
        """
        # AT+UMSA={0,1}
        buf = "AT+UMSA=1\r\n"
        resp: list[str] = self.write([buf.encode()]) # ty: ignore[invalid-assignment]
        if 'OK' not in resp:
            logger.error(resp)

    def unsetUsbMassStorage(self) -> None:
        """Disable USB mass storage mode on the BusyTag device.
        
        This method disables USB mass storage mode, preventing the BusyTag from
        appearing as a USB storage device when connected to a computer.
        
        Returns:
            None
            
        Example:
            >>> tag.unsetUsbMassStorage()
            # Disables USB mass storage mode
        """
        # AT+UMSA={0,1}
        buf = "AT+UMSA=0\r\n"
        resp: list[str] = self.write([buf.encode()]) # ty: ignore[invalid-assignment]
        if 'OK' not in resp:
            logger.error(resp)

    def getShowingPicture(self) -> str:
        """Get the currently showing picture filename from the BusyTag device.
        
        This method retrieves the name of the picture file that is currently
        being displayed on the BusyTag device.
        
        Returns:
            String containing the filename of the currently showing picture
            
        Example:
            "image.jpg"
        """
        # AT+SP?
        resp: list[str] = self.write([b'AT+SP?\r\n']) # ty: ignore[invalid-assignment]
        return resp[0]

    def setShowingPicture(self, filename: str) -> None:
        """Set the picture to be shown on the BusyTag device.
        
        This method configures the BusyTag to display a specific picture file
        stored on the device.
        
        Args:
            filename: String containing the name of the picture file to display
            
        Returns:
            None
            
        Example:
            >>> tag.setShowingPicture("image.jpg")
            # Displays image.jpg on the BusyTag
        """
        # AT+SP=filename
        buf = f"AT+SP={filename}\r\n"
        resp: list[str] = self.write([buf.encode()]) # ty: ignore[invalid-assignment]
        if 'OK' not in resp:
            logger.error(resp)

    def getAutoStorageScan(self) -> str:
        """Get the current auto storage scan configuration from the BusyTag device.
        
        This method retrieves the auto storage scan setting, which determines whether
        the BusyTag automatically scans for new files on the device.
        
        Returns:
            String containing the configuration value (0 or 1)
            
        Example:
            "1" (enabled)
        """
        # AT+AASS?
        resp: list[str] = self.write([b'AT+AASS?\r\n']) # ty: ignore[invalid-assignment]
        return resp[0]

    def setAutoStorageScan(self) -> None:
        """Enable auto storage scan on the BusyTag device.
        
        This method enables automatic storage device scanning, allowing it to detect
        new files automatically.
        
        Returns:
            None
            
        Example:
            >>> tag.setAutoStorageScan()
            # Enables automatic storage scan on startup
        """
        # AT+AASS={0,1}
        buf = "AT+AASS=1\r\n"
        resp: list[str] = self.write([buf.encode()]) # ty: ignore[invalid-assignment]
        if 'OK' not in resp:
            logger.error(resp)

    def unsetAutoStorageScan(self) -> None:
        """Disable auto storage scan on the BusyTag device.
        
        This method disables automatic storage device scanning.
        
        Returns:
            None
            
        Example:
            >>> tag.unsetAutoStorageScan()
            # Disables automatic storage scan on startup
        """
        # AT+AASS={0,1}
        buf = "AT+AASS=0\r\n"
        resp: list[str] = self.write([buf.encode()]) # ty: ignore[invalid-assignment]
        if 'OK' not in resp:
            logger.error(resp)

    # Actions

    def playPattern(self, active: bool = True, repeat: int = 255) -> None:
        """Play or stop the current pattern on the BusyTag device.
        
        This method controls whether the currently configured pattern should be 
        active or stopped on the BusyTag device.
        The pattern can be set to repeat a specified number of times or infinitely.
        
        Args:
            active: Boolean flag indicating whether to start (True) or stop (False)
                   the pattern playback (default: True)
            repeat: Integer specifying how many times to repeat the pattern (default: 255)
                   Use 255 for infinite repetition
           
        Returns:
            None
           
        Note:
            - The pattern to be played must be configured separately (e.g., via setCustomPattern)
            - Error responses are logged if the command fails
            - No confirmation is returned
           
        Example:
            >>> tag.playPattern(active=True, repeat=5)
            # Plays the current pattern 5 times
            >>> tag.playPattern(active=False)
            # Stops pattern playback
        """
        # AT+PP=allow,repeat
        # repeat 255 => infinite
        buf = f"AT+PP={1 if active else 0},{repeat}\r\n"
        resp: list[str] = self.write([buf.encode()]) # ty: ignore[invalid-assignment]
        if 'OK' not in resp:
            logger.error(resp)

    def getFile(self, filename: str, output_file: str | None = None) -> bytes | None:
        """Retrieve a file from the BusyTag device.
        
        This method downloads a file stored on the BusyTag device and can either
        return the file contents as bytes or save it directly to a local file.
        
        Args:
            filename: String containing the name of the file to retrieve from the device
            output_file: Optional string path where the file should be saved locally.
                        If None, the file contents are returned as bytes (default: None)
            
        Returns:
            bytes | None: If output_file is None, returns the file contents as bytes.
                      If output_file is specified, returns None and saves the file
                      to the specified path.
            
        Example:
            >>> # Get file and return as bytes
            >>> file_data = tag.getFile("image.jpg")
            >>> # Get file and save to disk
            >>> tag.getFile("image.jpg", "local_copy.jpg")
        """
        # AT+GF=filename
        buf = f"AT+GF={filename}\r\n"
        resp: list[bytes] = self.write([buf.encode()], binary=True) # ty: ignore[invalid-assignment]
        if output_file:
            with open(output_file, "wb") as f:
                f.write(b"".join(resp[2:-1]))
        else:
            return b"".join(resp[2:-1])

    def putFile(self, filepath: str) -> None:
        """Upload a file to the BusyTag device.
        
        This method uploads a local file to the BusyTag device's storage.
        The file is sent with its basename and size, allowing the device to
        store and manage it properly.
        
        Args:
            filepath: String containing the local path to the file to upload
            
        Returns:
            None
            
        Note:
            - The file is uploaded using the AT+UF command
            - Error responses are logged if the upload fails
            - Only the basename of the file is used on the device
            
        Example:
            >>> tag.putFile("/home/user/pictures/photo.jpg")
            # Uploads photo.jpg to the BusyTag device
        """
        # AT+UF=filename,size
        size = os.path.getsize(filepath)
        basename = os.path.basename(filepath)
        buf = [f"AT+UF={basename},{size}\r\n".encode()]
        with open(filepath, "rb") as f:
            buf.append(f.read())
        resp: list[str] = self.write(buf) # ty: ignore[invalid-assignment]
        
        if 'OK' not in resp:
            logger.error(resp)

    def deleteFile(self, filename: str) -> None:
        """Delete a file from the BusyTag device.
        
        This method removes a file from the BusyTag device's storage.
        The file is identified by its filename on the device.
        
        Args:
            filename: String containing the name of the file to delete from the device
            
        Returns:
            None
            
        Note:
            - The file is deleted using the AT+DF command
            - Error responses are logged if the deletion fails
            - No confirmation is returned; check file list to verify deletion
            
        Example:
            >>> tag.deleteFile("old_image.jpg")
            # Deletes old_image.jpg from the BusyTag device
        """
        # AT+DF=filename
        buf = f"AT+DF={filename}\r\n"
        resp: list[str] = self.write([buf.encode()]) # ty: ignore[invalid-assignment]
        if 'OK' not in resp:
            logger.error(resp)

    def restart(self) -> None:
        """Restart the BusyTag device.
        
        This method sends a restart command to the BusyTag device, causing it to
        reboot. The device will be unavailable during the restart process.
        
        Returns:
            None
            
        Note:
            - The device will reboot and reconnect
            - Error responses are logged if the restart fails
            - No confirmation is returned; the device will automatically restart
            
        Example:
            >>> tag.restart()
            # Restarts the BusyTag device
        """
        # AT+RST
        buf = b"AT+RST\r\n"
        resp: list[str] = self.write([buf]) # ty: ignore[invalid-assignment]
        if 'OK' not in resp:
            logger.error(resp)

    def formatDeviceStorage(self) -> None:
        """Format the storage on the BusyTag device.
        
        This method sends a command to format the internal storage of the BusyTag device.
        All files and configurations will be erased. Use with caution.
        
        Returns:
            None
            
        Note:
            - All files and configurations will be permanently deleted
            - Error responses are logged if the formatting fails
            - No confirmation is returned
            
        Example:
            >>> tag.formatDeviceStorage()
            # Formats the BusyTag device storage
        """
        # AT+FD
        buf = b"AT+FD\r\n"
        resp: list[str] = self.write([buf]) # ty: ignore[invalid-assignment]
        if 'OK' not in resp:
            logger.error(resp)

    def activateFileStorageScan(self) -> None:
        """Activate file storage scan on the BusyTag device.
        
        This method triggers a manual scan of the device's storage to detect and
        register any new files that have been added.
        
        Returns:
            None
            
        Note:
            - Useful after manually adding files via USB mass storage
            - Error responses are logged if the scan fails
            - No confirmation is returned
            
        Example:
            >>> tag.activateFileStorageScan()
            # Triggers a manual file storage scan
        """
        # AT+AFSS
        buf = b"AT+AFSS\r\n"
        resp: list[str] = self.write([buf]) # ty: ignore[invalid-assignment]
        if 'OK' not in resp:
            logger.error(resp)

    def factoryResetMainConfig(self) -> None:
        """Reset the main configuration to factory defaults.
        
        This method resets all main configuration settings (LED patterns, brightness,
        etc.) to their factory default values. WiFi and file storage configurations
        are not affected.
        
        Returns:
            None
            
        Note:
            - Only main configuration settings are reset
            - WiFi and file storage configurations remain unchanged
            - Error responses are logged if the reset fails
            - No confirmation is returned
            
        Example:
            >>> tag.factoryResetMainConfig()
            # Resets main configuration to factory defaults
        """
        # AT+FRMCF
        buf = b"AT+FRMCF\r\n"
        resp: list[str] = self.write([buf]) # ty: ignore[invalid-assignment]
        if 'OK' not in resp:
            logger.error(resp)

    def factoryResetWifiConfig(self) -> None:
        """Reset the WiFi configuration to factory defaults.
        
        This method resets the WiFi SSID and password to their factory default values.
        Main configuration and file storage settings are not affected.
        
        Returns:
            None
            
        Note:
            - Only WiFi configuration settings are reset
            - Main configuration and file storage remain unchanged
            - Error responses are logged if the reset fails
            - No confirmation is returned
            
        Example:
            >>> tag.factoryResetWifiConfig()
            # Resets WiFi configuration to factory defaults
        """
        # AT+FRWCF
        buf = b"AT+FRWCF\r\n"
        resp: list[str] = self.write([buf]) # ty: ignore[invalid-assignment]
        if 'OK' not in resp:
            logger.error(resp)

    def factoryResetDefaultImage(self) -> None:
        """Reset the default image to factory defaults.
        
        This method resets the default image displayed on the BusyTag device to
        the factory default image. All other configurations remain unchanged.
        
        Returns:
            None
            
        Note:
            - Only the default image is reset
            - All other configurations remain unchanged
            - Error responses are logged if the reset fails
            - No confirmation is returned
            
        Example:
            >>> tag.factoryResetDefaultImage()
            # Resets the default image to factory defaults
        """
        # AT+FRDI
        buf = b"AT+FRWCF\r\n"
        resp: list[str] = self.write([buf]) # ty: ignore[invalid-assignment]
        if 'OK' not in resp:
            logger.error(resp)

class BusyTagPattern:
    def __init__(self, leds: List[BusyTag.LEDS] = [BusyTag.LEDS.ALL], color: str = "FFFFFF", scale: float = 1.0, speed: int = 100, delay: int = 0):
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

