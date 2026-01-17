# BusyTag GUI

A graphical user interface for controlling BusyTag devices.

## Features

- **Device Connection**: Connect to BusyTag devices via serial port
- **LED Control**: Set LED colors and brightness
- **LED Pattern**: Play and stop custom LED patterns
- **Picture Management**: Upload, list, display, and delete pictures
- **Device Information**: View device details and firmware version

## Usage

Run the GUI application:

```bash
uv run gui.py
```

### Main Interface

1. **Device Connection**
   - Select a serial port from the dropdown
   - Click "Refresh" to scan for available ports
   - Click "Connect" to establish connection

2. **LED Control**
   - Enter a color in hex format (e.g., "FF0000" for red, "F00" for red)
   - Click "Pick Color" to open a color picker dialog
   - Click "Set Color" to apply the color
   - Select which LEDs to control (All or individual LEDs 0-6)
   - Set brightness percentage (1-100) and click "Set Brightness"

3. **LED Pattern**
   - Select a pattern from the dropdown (DEFAULT, POLICE_1, etc.)
   - Set the repeat count (default: 255 => infinite)
   - Click "Play Pattern" to start the pattern
   - Click "Stop Pattern" to stop the current pattern

4. **Picture Management**
   - Click "List Pictures" to view available pictures
   - Click "Upload Picture" to upload a new image (supports JPG, JPEG, PNG, BMP, GIF) size 240x280
   - Select a picture from the list and click "Display Picture" to show it
   - Select a picture from the list and click "Delete Picture" to remove it

5. **Device Information**
   - View device ID, name, manufacturer, and firmware version

## Requirements

- Python 3.x
- Tkinter (usually included with Python)
- pyserial
- ttkbootstrap (for modern UI styling)

## Installation

Install dependencies:

```bash
uv sync
```

## Command Line Alternative

For command-line usage, see the main [README.md](README.md) file.
