# Preset Configuration File Support

The `config` command allows you to apply a batch of configurations from a YAML file to your BusyTag device.

## Usage

```bash
busytag-cli --device /dev/ttyUSB0 preset preset.yaml
```

## Configuration File Format

The configuration file is a YAML file that can contain the following optional fields:

### `image` (optional)
Path to an image file to upload and display.

**Example:** `image: image.jpg`

### `solid_colors` (optional)
An array of solid color configurations to apply.

Each color configuration can have:
- `color`: Color value (hex string, e.g., "FF0000" for red)
- `leds`: Array of LEDs to apply the color to (e.g., ["all"], ["LED1", "LED3", "LED5"])
- `dim`: Brightness scale (0.0 - 1.0, default: 1.0)
- `reset`: Whether to reset all LEDs before setting color (default: True)

**Example:**
```yaml
solid_colors:
  - color: FF0000
    leds: [all]
    dim: 1.0
    reset: true
```

### `pattern` (optional)
Sets one or more LED patterns to play in sequence. You can use predefined patterns or define custom patterns.

**Example (single pattern):** `pattern: RED_FLASHES`

**Example (multiple patterns):**
```yaml
pattern:
  - RED_FLASHES
  - BLUE_FLASHES
  - GREEN_FLASHES
```

**Example (custom pattern):**
```yaml
pattern:
  - color: FF0000
    leds: [all]
    speed: 50
    delay: 10
```

**Example (mixed patterns):**
```yaml
pattern:
  - RED_FLASHES
  - color: 00FF00
    leds: [all]
    speed: 100
    delay: 0
  - BLUE_PULSES
```

When multiple patterns are specified, they are merged and played in sequence. 

*Note:* merging predefined patterns works less good.

Custom pattern fields:
- `color`: Color value (hex string, e.g., "FF0000" for red, default: "FFFFFF")
- `leds`: Array of LEDs to apply the pattern to (e.g., ["all"], ["0", "1", "2"], default: ["all"])
- `speed`: Pattern speed (integer, default: 100)
- `delay`: Delay between pattern steps (integer, default: 0)
- `dim`: Brightness scale (0.0 - 1.0, default: 1.0)

### `repeat` (optional)
Number of times to repeat the pattern sequence (default: 255 for infinite).

**Example:** `repeat: 5`

## Complete Example

```yaml
image: image.jpg
solid_colors:
  - color: FF0000
    leds: [all]
    dim: 1.0
    reset: true
pattern: RED_FLASHES
repeat: 5
```

## Available Patterns

- `DEFAULT`
- `POLICE_1`, `POLICE_2`
- `RED_FLASHES`, `GREEN_FLASHES`, `BLUE_FLASHES`, `YELLOW_FLASHES`, `CYAN_FLASHES`, `MAGENTA_FLASHES`, `WHITE_FLASHES`
- `RED_PULSES`, `GREEN_PULSES`, `BLUE_PULSES`, `YELLOW_PULSES`, `CYAN_PULSES`, `MAGENTA_PULSES`, `WHITE_PULSES`
- `RED_RUNNING`, `GREEN_RUNNING`, `BLUE_RUNNING`, `YELLOW_RUNNING`, `CYAN_RUNNING`, `MAGENTA_RUNNING`, `WHITE_RUNNING`

## Notes

- All fields are optional - you can include just the configurations you want to change
- If an image file is specified but not found, it will be skipped with a warning
- If a pattern name is not recognized, an error will be shown with available patterns
- The configuration is applied in order: device name, image, solid colors, pattern
