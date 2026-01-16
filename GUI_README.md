# BusyTag GUI

A graphical user interface for controlling BusyTag devices.

## Features

- **Device Connection**: Connect to BusyTag devices via serial port
- **LED Control**: Set LED colors and brightness
- **Picture Management**: Upload, list, display, and delete pictures
- **Device Information**: View device details and firmware version

## Usage

Run the GUI application:

```bash
python gui.py
```

### Main Interface

1. **Device Connection**
   - Select a serial port from the dropdown
   - Click "Refresh" to scan for available ports
   - Click "Connect" to establish connection

2. **LED Control**
   - Enter a color in hex format (e.g., "FF0000" for red, "F00" for red)
   - Select which LEDs to control (All or individual LEDs)
   - Click "Set Color" to apply
   - Set brightness percentage (1-100) and click "Set Brightness"

3. **Picture Management**
   - Click "List Pictures" to view available pictures
   - Click "Upload Picture" to upload a new image
   - Select a picture from the list and click "Display Picture" to show it
   - Select a picture from the list and click "Delete Picture" to remove it

4. **Device Information**
   - View device ID, name, manufacturer, and firmware version

## Requirements

- Python 3.x
- Tkinter (usually included with Python)
- pyserial
- webcolors

## Installation

Install dependencies:

```bash
pip install pyserial webcolors
```

## Command Line Alternative

For command-line usage, see the main [README.md](README.md) file.
