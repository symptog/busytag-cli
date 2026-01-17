# Busy Tag - CLI

**Important**: This is just a side project and not maintained regularly.

This repository provides a Python based CLI util and library to communicate with the [SID Busy Tag](https://www.busy-tag.com/) serial interface.

## Usage

### Command Line Interface

```bash
uv sync
uv run main.py
```

```
usage: main.py [-h] [--debug] --device DEVICE [--json] {show,pictures,led,led-pattern,raw} ...

positional arguments:
  {show,pictures,led,led-pattern,raw}
    show                Show Information
    pictures            Interact with Pictures
    led                 Interact with LEDs
    led-pattern         Interact with LED Patterns
    raw                 Send raw command

options:
  -h, --help            show this help message and exit
  --debug
  --device DEVICE
  --json
```

### Graphical User Interface (Alpha)

```bash
uv run gui.py
```

See [GUI_README.md](GUI_README.md) for more information about the GUI.

### Show Device Information

Get device information.

```bash
uv run main.py --device /dev/ttyACM0 show 
ID: 34B7DA612B1C
Name: busytag-612B1C
Manufacture: GREYNUT LTD
Firmware: 1.0
```

```bash
uv run main.py --device /dev/ttyACM0 --json show
{"id": "34B7DA612B1C", "name": "busytag-612B1C", "manufacture": "GREYNUT LTD", "firmware_version": "1.0"}
```

### Interact with LEDs

```bash
uv run main.py --device /dev/ttyACM0 led --help
usage: main.py led [-h] {on,off} ...

positional arguments:
  {on,off}
    on        Set LEDs On
    off       Set LEDs Off

options:
  -h, --help  show this help message and exit
```

#### LEDs ON

Set all or some leds on with the definded color. Optionally reset all leds before changing the color.

```bash
uv run main.py --device /dev/ttyACM0 led on --help    
usage: main.py led on [-h] [--dim DIM] [--reset] [--led {all,0,1,2,3,4,5,6} [{all,0,1,2,3,4,5,6} ...]] color

positional arguments:
  color                 Color Value

options:
  -h, --help            show this help message and exit
  --dim DIM             LED brightness 0.0 - 1.0 (Default: 1.0)
  --reset               Reset all LEDs befor setting color (Default: False)
  --led {all,0,1,2,3,4,5,6} [{all,0,1,2,3,4,5,6} ...]
                        LEDs to set (Default: all)
```

##### Example

```bash
uv run main.py --debug --device /dev/ttyACM0 led on yellow --reset --led 0 2 4 6 --dim 0.1
```


#### LEDs OFF

Turn all leds off.

```
uv run main.py --device /dev/ttyACM0 led off
```

#### LED Pattern

```bash
uv run main.py --device /dev/ttyACM0 led-pattern --help
usage: main.py led-pattern [-h] {on,off} ...

positional arguments:
  {on,off}
    on        Set LED Pattern
    off       Stop LED Pattern

options:
  -h, --help  show this help message and exit
```

```bash
uv run main.py --device /dev/ttyACM0 led-pattern on --help
usage: main.py led-pattern on [-h] [--repeat REPEAT] pattern

positional arguments:
  pattern          Pattern Name

options:
  -h, --help       show this help message and exit
  --repeat REPEAT  Repeat Pattern n times
```

##### Example

```bash
uv run main.py --device /dev/ttyACM0 led-pattern on DEFAULT --repeat 5
```

#### Available Pattern

```
DEFAULT
POLICE_1
POLICE_2
RED_FLASHES
GREEN_FLASHES
BLUE_FLASHES
YELLOW_FLASHES
CYAN_FLASHES
MAGENTA_FLASHES
WHITE_FLASHES
RED_PULSES
GREEN_PULSES
BLUE_PULSES
YELLOW_PULSES
CYAN_PULSES
MAGENTA_PULSES
WHITE_PULSES
RED_RUNNING
GREEN_RUNNING
BLUE_RUNNING
YELLOW_RUNNING
CYAN_RUNNING
MAGENTA_RUNNING
WHITE_RUNNING
```

### Interacting with Pictures

```bash
uv run main.py --device /dev/ttyACM0 pictures --help
usage: main.py pictures [-h] {list,upload,display,delete} ...

positional arguments:
  {list,upload,display,delete}
    list                List Pictures
    upload              Upload Picture
    display             Display Picture
    delete              Delete Picture

options:
  -h, --help            show this help message and exit
```

#### List Pictures (on device)

List all pictures that are available on the device.


```bash
uv run main.py --device /dev/ttyACM0 pictures list 
def.png (15.84 kB)
fry.gif (14.32 kB)
```

```bash
uv run main.py --device /dev/ttyACM0 --json pictures list
[{"name": "def.png", "size": 16224}, {"name": "fry.gif", "size": 14665}]
```

#### Upload Picture

Upload a picture to the device. Optionaly set it as a background once uploaded.

Pictures must be of size 240x280px

```bash
uv run main.py --device /dev/ttyACM0 pictures upload --help
usage: main.py pictures upload [-h] [--use] filename

positional arguments:
  filename    Path to file for upload

options:
  -h, --help  show this help message and exit
  --use       Set Picture as Background
```

##### Example

```bash
uv run main.py --device /dev/ttyACM0 pictures upload --use ./fry.gif
```

#### Display Picture

Set a picture as background on the device. Picture must already be present.

```bash
uv run main.py --device /dev/ttyACM0 pictures display fry.gif
```

#### Delete Picture

Delete picture from device.

```bash
uv run main.py --device /dev/ttyACM0 pictures delete fry.gif
```

### Raw Command

Send raw AT commands to the device.

```bash
uv run main.py --device /dev/ttyACM0 raw --help
usage: main.py raw [-h] [--json] command

positional arguments:
  command              Command to send

options:
  -h, --help           show this help message and exit
  --json                Output result as JSON
```

##### Example

```bash
uv run main.py --device /dev/ttyACM0 raw "AT+GDN"
```

## API

The `BusyTag` class implements most AT commands as definded in this documentation:

https://luxafor.helpscoutdocs.com/article/47-busy-tag-usb-cdc-command-reference-guide

Not all methods are fully tested. Some functionality are not documented.

```
def write(self, data: list[bytes], binary=False):
def showDeviceInfo(self):
def getDeviceName(self):
def getManufactureName(self):
def getDeviceId(self):
def getFirmwareVersion(self):
def getPictureList(self):
def getFileList(self):
def getLocalHostAddress(self):
def getFreeStorageSize(self):
def getTotalStorageSize(self):
def getLastErrorCode(self):
def getLastResetReasonCore0(self):
def getLastResetReasonCore1(self):
def getSolidColor(self):
def setSolidColor(self, color="red", scale = 1.0, leds=[LEDS.ALL], clear=True):
def getCustomPattern(self):
def setCustomPattern(self, patterns=[], repeat=255):
def getDisplayBrightness(self):
def setDisplayBrightness(self, brightness=100):
def getShowAfterDrop(self):
def setShowAfterDrop(self):
def unsetShowAfterDrop(self):
def getAllowWebFileServer(self):
def setAllowWebFileServer(self):
def unsetAllowWebFileServer(self):
def getWifiConfig(self):
def setWifiConfig(self, ssid, password):
def getUsbMassStorage(self):
def setUsbMassStorage(self):
def unsetUsbMassStorage(self):
def getShowingPicture(self):
def setShowingPicture(self, filename):
def getAutoStorageScan(self):
def setAutoStorageScan(self):
def unsetAutoStorageScan(self):
def playPattern(self, allow=True, repeat=255):
def getFile(self, filename, output_file=None):
def putFile(self, filepath):
def deleteFile(self, filename):
def restart(self):
def formatDeviceStorage(self):
def activateFileStorageScan(self):
def factoryResetMainConfig(self):
def factoryResetWifiConfig(self):
def factoryResetDefaultImage(self):
```

### Example

```python
from .busytag import BusyTag
import os

bt = BusyTag("/dev/ttyACM0")
print(bt.showDeviceInfo())

# Change LED Color
bt.setSolidColor("red", scale=0.5, leds=[BusyTag.LEDS.ALL], clear=True)

# Upload Picture
filename = "./fry.gif"
bt.putFile(filename)

# Set Picture as Background
fname = os.path.basename(filename)
bt.setShowingPicture(fname)
```
