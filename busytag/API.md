# API Reference

## BusyTag Class

Main class for controlling BusyTag devices via serial communication and file management.

### Constructor

```python
BusyTag(device: str, baudrate: int = 115200, timeout: int = 1, keep_serial: bool = True)
```

**Parameters:**
- `device` (str): Serial device path (e.g., '/dev/ttyUSB0', '/dev/ttyUSB1')
- `baudrate` (int): Baud rate for serial communication (default: 115200)
- `timeout` (int): Timeout in seconds for serial operations (default: 1)
- `keep_serial` (bool): Whether to keep serial connection open after each write (default: True)

**Returns:** BusyTag instance

### Mount Methods

#### mount()
Mount the BusyTag storage device and prepare it for file operations.

```python
mount() -> bool
```

**Returns:** True if mounted successfully, False otherwise

**Behavior:**
- Checks for existing mount and returns immediately if found
- Enables USB mass storage if disabled
- Enables auto storage scan if disabled
- Scans for BusyTag device in /sys/class/block
- Sets `self.mount_path` to the mount point if found

#### activateFileStorageScan()
Trigger a manual file storage scan to detect new files.

```python
activateFileStorageScan() -> bool
```

**Returns:** True if scan activated successfully

#### getUsbMassStorage()
Get USB mass storage configuration value.

```python
getUsbMassStorage() -> str
```

**Returns:** "0" (disabled) or "1" (enabled)

#### setUsbMassStorage()
Enable USB mass storage mode on the device.

```python
setUsbMassStorage(active: bool = True) -> bool
```

**Parameters:**
- `active` (bool): Enable (True) or disable (False) mass storage

**Returns:** True if enabled successfully

**Note:** Device may reset during this operation

#### getAutoStorageScan()
Get auto storage scan configuration.

```python
getAutoStorageScan() -> str
```

**Returns:** "0" (disabled) or "1" (enabled)

#### setAutoStorageScan()
Enable automatic storage device scanning.

```python
setAutoStorageScan(active: bool = True) -> bool
```

**Returns:** True if enabled successfully

### Device Information Methods

#### showDeviceInfo()
Get comprehensive device information.

```python
showDeviceInfo() -> Dict[str, str]
```

**Returns:** Dictionary with keys:
- `id`: Device ID string
- `name`: Device name
- `manufacture`: Manufacturer name
- `firmware_version`: Firmware version

#### getDeviceName()
Get the device name.

```python
getDeviceName() -> str
```

**Returns:** Device name string

#### getDeviceId()
Get the unique device ID.

```python
getDeviceId() -> str
```

**Returns:** Device ID string

#### getFirmwareVersion()
Get the firmware version.

```python
getFirmwareVersion() -> str
```

**Returns:** Firmware version string

#### getLocalHostAddress()
Get the local host IP address.

```python
getLocalHostAddress() -> str
```

**Returns:** IP address string

#### getFreeStorageSize()
Get available storage size in bytes.

```python
getFreeStorageSize() -> str
```

**Returns:** Free storage size in bytes

#### getTotalStorageSize()
Get total storage size in bytes.

```python
getTotalStorageSize() -> str
```

**Returns:** Total storage size in bytes

#### getLastErrorCode()
Get the last error code from the device.

```python
getLastErrorCode() -> ErrorCode
```

**Returns:** ErrorCode enum value

### LED Control Methods

#### setSolidColor()
Set a solid color on specified LEDs.

```python
setSolidColor(color: str = "red", scale: float = 1.0, leds: List = [LEDS.ALL], clear: bool = True) -> bool
```

**Parameters:**
- `color` (str): Color name (e.g., "red", "blue") or hex value
- `scale` (float): Brightness scale (0.0-1.0, default: 1.0)
- `leds` (List[LEDS]): List of LED patterns to target (default: all LEDs)
- `clear` (bool): Clear all LEDs to black first (default: True)

**Returns:** True if set successfully

**LED Values for `leds` parameter:**
- `LEDS.ALL` (127): All LEDs
- `LEDS.LED0` (1): LED 0
- `LEDS.LED1` (2): LED 1
- `LEDS.LED2` (4): LED 2
- `LEDS.LED3` (8): LED 3
- `LEDS.LED4` (16): LED 4
- `LEDS.LED5` (32): LED 5
- `LEDS.LED6` (64): LED 6
- `LEDS.LEFT` (15): Left group (LEDs 0-2)
- `LEDS.RIGHT` (120): Right group (LEDs 5-6)

#### getSolidColor()
Get current solid color configuration.

```python
getSolidColor() -> str
```

**Returns:** Color configuration string (e.g., "127,FF0000")

#### setCustomPattern()
Set a custom LED pattern sequence.

```python
setCustomPattern(patterns: List, repeat: int = 255, active: bool = True) -> bool
```

**Parameters:**
- `patterns` (List[BusyTagPattern]): List of BusyTagPattern objects
- `repeat` (int): Number of times to repeat (default: 255 = infinite)
- `active` (bool): Start playback immediately (default: True)

**Returns:** True if set successfully

#### getCustomPattern()
Get current custom pattern configuration.

```python
getCustomPattern() -> List[BusyTagPattern]
```

**Returns:** List of BusyTagPattern objects

#### playPattern()
Play or stop the current pattern.

```python
playPattern(active: bool = True, repeat: int = 255) -> bool
```

**Parameters:**
- `active` (bool): True to play, False to stop (default: True)
- `repeat` (int): Repeat count (default: 255 = infinite)

**Returns:** True if command executed successfully

**Note:** You must set the pattern before calling this method

#### getDisplayBrightness()
Get current display brightness level.

```python
getDisplayBrightness() -> str
```

**Returns:** Brightness value (0-100)

#### setDisplayBrightness()
Set display brightness level.

```python
setDisplayBrightness(brightness: int = 100) -> bool
```

**Parameters:**
- `brightness` (int): Brightness level (1-100, default: 100)

**Returns:** True if set successfully

### File Management Methods

#### getFileList()
Get list of files stored on the device.

```python
getFileList() -> List[Dict]
```

**Returns:** List of dictionaries with keys:
- `name`: File name
- `size`: File size in bytes
- `type`: File type

#### getPictureList()
Get list of picture files on the device.

```python
getPictureList() -> List[Dict]
```

**Returns:** List of dictionaries with names and sizes

#### getFile()
Download a file from the device.

```python
getFile(filename: str, output_file: str | None = None) -> bytes | None
```

**Parameters:**
- `filename` (str): File name on device
- `output_file` (str): Optional local file path to save to

**Returns:**
- If `output_file` is None: Returns file contents as bytes
- If `output_file` is specified: Returns None and saves file

#### putFile()
Upload a file to the device.

```python
putFile(filepath: str, override: bool = False) -> bool
```

**Parameters:**
- `filepath` (str): Local file path to upload
- `override` (bool): Overwrite if file exists (default: False)

**Returns:** True if uploaded successfully

**Note:** Only basename of file is used on device; must be ≤30 characters

#### putFileFromUrl()
Download a file from URL and upload to device.

```python
putFileFromUrl(url: str, filename: str | None = None, override: bool = False) -> bool
```

**Parameters:**
- `url` (str): URL to download from
- `filename` (str): Optional filename on device
- `override` (bool): Overwrite if exists (default: False)

**Returns:** True if upload successful

#### deleteFile()
Delete a file from the device.

```python
deleteFile(filename: str) -> bool
```

**Parameters:**
- `filename` (str): File name to delete

**Returns:** True if deleted successfully

#### deleteFile() is equivalent to AT+DF command, no confirmation returned.

### Configuration Methods

#### setWifiConfig()
Configure WiFi connection.

```python
setWifiConfig(ssid: str, password: str) -> bool
```

**Parameters:**
- `ssid` (str): WiFi network name
- `password` (str): WiFi password

**Returns:** True if configured successfully

#### getWifiConfig()
Get current WiFi configuration.

```python
getWifiConfig() -> str
```

**Returns:** WiFi configuration string (e.g., "ssid,password")

#### setShowAfterDrop()
Enable automatic display after drop event.

```python
setShowAfterDrop(active: bool = True) -> bool
```

**Parameters:**
- `active` (bool): Enable (True) or disable (False)

**Returns:** True if enabled successfully

**Note:** Undefined Behavior

#### getShowAfterDrop()
Get "Show After Drop" configuration.

```python
getShowAfterDrop() -> str
```

**Returns:** Configuration value ("0" or "1")

**Note:** Undefined Behavior

#### setAllowWebFileServer()
Enable web file server access.

```python
setAllowWebFileServer(active: bool = True) -> bool
```

**Parameters:**
- `active` (bool): Enable (True) or disable (False)

**Returns:** True if enabled successfully

#### getAllowWebFileServer()
Get web file server configuration.

```python
getAllowWebFileServer() -> str
```

**Returns:** Configuration value ("0" or "1")

#### setShowingPicture()
Set the picture to display.

```python
setShowingPicture(filename: str) -> bool
```

**Parameters:**
- `filename` (str): Picture filename to display

**Returns:** True if set successfully

#### getShowingPicture()
Get currently displayed picture filename.

```python
getShowingPicture() -> str
```

**Returns:** Filename of currently showing picture

### System Methods

#### restart()
Restart the device.

```python
restart() -> bool
```

**Returns:** True if restart initiated successfully

**Note:** Device will reboot and reconnect

#### formatDeviceStorage()
Format all device storage.

```python
formatDeviceStorage() -> bool
```

**Returns:** True if formatting initiated successfully

**Warning:** All files and configurations will be permanently deleted

#### factoryResetMainConfig()
Reset main configuration to factory defaults.

```python
factoryResetMainConfig() -> bool
```

**Returns:** True if reset successful

**Note:** Only main configuration; WiFi and files remain unchanged

#### factoryResetWifiConfig()
Reset WiFi to factory defaults.

```python
factoryResetWifiConfig() -> bool
```

**Returns:** True if reset successful

**Note:** Only WiFi configuration; other settings remain

#### factoryResetDefaultImage()
Reset default image to factory settings.

```python
factoryResetDefaultImage() -> bool
```

**Returns:** True if reset successful

**Note:** Only default image; other settings remain

## BusyTagPattern Class

Represents a custom LED pattern for the BusyTag device.

### Constructor

```python
BusyTagPattern(
    leds: List = [BusyTag.LEDS.ALL],
    color: str = "FFFFFF",
    scale: float = 1.0,
    speed: int = 100,
    delay: int = 0
)
```

**Parameters:**
- `leds` (List[LEDS]): LEDs to light
- `color` (str): Color hex value (e.g., "FFFFFF", "FF0000")
- `scale` (float): Color brightness scale (0.0-1.0)
- `speed` (int): Speed setting (1-150)
- `delay` (int): Delay between pattern steps (0-255)

**Returns:** BusyTagPattern instance

### Methods

#### __str__()
Get string representation for device transmission.

**Returns:** Formatted string "led_mask,color_hex,speed,delay"

#### __repr__()
Get official string representation.

**Returns:** Formatted string "led_mask,color_hex,speed,delay"

## BusyTagDefaultPattern Enum

Predefined LED patterns for common scenarios.

### Pattern Constants

* `DEFAULT` 
* `POLICE_1`
* `POLICE_2`
* `RED_FLASHES`
* `GREEN_FLASHES`
* `BLUE_FLASHES`
* `YELLOW_FLASHES`
* `CYAN_FLASHES`
* `MAGENTA_FLASHES`
* `WHITE_FLASHES`
* `RED_PULSES`
* `GREEN_PULSES`
* `BLUE_PULSES`
* `YELLOW_PULSES`
* `CYAN_PULSES`
* `MAGENTA_PULSES`
* `WHITE_PULSES`
* `RED_RUNNING`
* `GREEN_RUNNING`
* `BLUE_RUNNING`
* `YELLOW_RUNNING`
* `CYAN_RUNNING`
* `MAGENTA_RUNNING`
* `WHITE_RUNNING`


## LED Enum

Bitmask values for individual LEDs and patterns.

### LED Bitmasks

- `LEDS.ALL` (127): All 7 LEDs
- `LEDS.LED0` (1): Single LED 0
- `LEDS.LED1` (2): Single LED 1
- `LEDS.LED2` (4): Single LED 2
- `LEDS.LED3` (8): Single LED 3
- `LEDS.LED4` (16): Single LED 4
- `LEDS.LED5` (32): Single LED 5
- `LEDS.LED6` (64): Single LED 6

### Group Patterns

- `LEDS.LEFT` (15): Left group (LEDs 0-2)
- `LEDS.RIGHT` (120): Right group (LEDs 5-6)

### Running Patterns

- `LEDS.RUN0` (129): Running head starting at LED 0
- `LEDS.RUN1` (130): Running head starting at LED 1
- `LEDS.RUN2` (132): Running head starting at LED 2
- `LEDS.RUN3` (136): Running head starting at LED 3
- `LEDS.RUN4` (144): Running head starting at LED 4
- `LEDS.RUN5` (160): Running head starting at LED 5
- `LEDS.RUN6` (192): Running head starting at LED 6

## ErrorCode Enum

Potential error codes returned by the device.

- `NONE` (-1): No error
- `UNKNOWN_ERROR` (0): Unknown error
- `UNKNOWN_COMMAND` (1): Unknown command
- `INVALID_ARGUMENT` (2): Invalid argument
- `FILE_NOT_FOUND` (3): File not found
- `INVALID_SIZE` (4): Invalid size

## ResetReason Enum

Reasons for device reset.

- `POWER_ON_RESET` (1): Power on
- `SOFTWARE_RESETS_DIGITAL_CORE` (3): Software reset (digital core)
- `DEEP_SLEEP_RESETS_DIGITAL_CORE` (5): Deep sleep reset
- `SDIO_MODULE_RESETS_DIGITAL_CORE` (6): SDIO module reset
- `MAIN_WATCHDOG_0_RESETS_DIGITAL_CORE` (7): Watchdog reset 0
- `MAIN_WATCHDOG_1_RESETS_DIGITAL_CORE` (8): Watchdog reset 1
- `RTC_WATCHDOG_RESETS_DIGITAL_CORE` (9): RTC watchdog reset
- `MAIN_WATCHDOG_RESETS_CPU` (11): Watchdog reset (CPU)
- `SOFTWARE_RESETS_CPU` (12): Software reset (CPU)
- `RTC_WATCHDOG_RESETS_CPU` (13): RTC watchdog reset (CPU)
- `CPU0_RESETS_CPU1` (14): CPU0 to CPU1 reset
- `VDD_VOLTAGE_UNSTABLE` (15): Voltage instability
- `RTC_WATCHDOG_RESETS_DIGITAL_CORE_AND_TC_MODULE` (16): Multiple watchdog reset

## Additional Classes

## BusyTagPattern class in color.py

The `BusyTagPattern` class in `color.py` handles color parsing and scaling.

### color.parse_color_string()

Convert color strings to RGB values with optional scaling.

```python
parse_color_string(value: str, scale: float = 1.0) -> Tuple[int, int, int]
```

**Parameters:**
- `value` (str): Color name or hex value
- `scale` (float): Brightness scale (0.0-1.0)

**Returns:** Tuple of (r, g, b) RGB values

**Supported formats:**
- Color names: e.g., "red", "blue", "green"
- Hex values: e.g., "#FF0000", "0xFF0000", "FF0000", "#FF"

### color.colortuple_to_name()

Convert RGB tuple to color name or hex string.

```python
colortuple_to_name(color: Tuple[int, int, int]) -> str
```

**Returns:** Color name if recognized, otherwise hex string

### color.scale_color()

Scale RGB values by brightness factor.

```python
scale_color(color: Tuple[int, int, int], scale: float = 1.0) -> Tuple[int, int, int]
```

**Parameters:**
- `color` (Tuple): RGB values
- `scale` (float): Brightness factor (0.0-1.0)

**Returns:** Scaled RGB values (0-255 range)

### ColorLookupError

Exception raised when color string cannot be parsed