#!/bin/env python3
# SPDX-License-Identifier: MIT

from busytag import BusyTag, BusyTagDefaultPattern, BusyTagPattern

import sys
import os
import yaml
import json
from urllib.parse import urlparse, parse_qs

import logging
logger = logging.getLogger(__name__)
 
def show_command(args, bt):
    logger.debug(args)
    dev = bt.showDeviceInfo()
    if args.json:
        print(json.dumps(dev))
    else:
        print(f"ID: {dev["id"]}")
        print(f"Name: {dev["name"]}")
        print(f"Manufacture: {dev["manufacture"]}")
        print(f"Firmware: {dev["firmware_version"]}")

def picture_command(args, bt):
    logger.debug(args)
    if not args.pcommand or args.pcommand == "list":
        pics = bt.getPictureList()
        if args.json:
            print(json.dumps(pics))
        else:
            for p in pics:
                kb_size = p["size"]/1024
                print(f"{p["name"]} ({kb_size:.2f} kB)")
    elif args.pcommand == "upload":
        bt.mount()
        bt.putFile(args.filename)
        fname = os.path.basename(args.filename)
        if args.use:
            bt.setShowingPicture(fname)
    elif args.pcommand == "display":
        bt.setShowingPicture(args.filename)
    elif args.pcommand == "delete":
        bt.deleteFile(args.filename)
    else:
        pass

def led_command(args, bt):
    logger.debug(args)
    if args.lcommand == "on":
        leds = []
        if "all" in args.led:
            leds = [BusyTag.LEDS.ALL]
        else:
            for i in args.led:
                num = int(i)
                leds.append(BusyTag.LEDS(2**num))
        bt.setSolidColor(args.color, scale=args.dim, leds=leds, clear=args.reset)
    elif args.lcommand == "off":
        bt.setSolidColor("000000", clear=False)

def led_pattern_command(args, bt):
    logger.debug(args)
    if args.lpcommand == "on":
        try:
            pattern = BusyTagDefaultPattern[args.pattern.upper()]
            bt.setCustomPattern(pattern.value, args.repeat)
        except KeyError as e:
            print("Available Pattern:")
            for p in BusyTagDefaultPattern:
                print(p.name)
    elif args.lpcommand == "off":
        bt.playPattern(0,0)
    
def raw_command(args, bt):
    logger.debug(args)
    result = bt.write([f"{args.command}\r\n".encode()])
    if args.json:
        print(json.dumps(result))
    else:
        print(result)
    
def preset_command(args, bt):
    logger.debug(args)
    
    # Read config file
    try:
        with open(args.preset_file, 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: File '{args.preset_file}' not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in config file: {e}")
        sys.exit(1)
    
    # Upload image if specified
    if 'image' in config:
        image_path = config['image']
        if os.path.exists(image_path):
            bt.mount()
            bt.putFile(image_path)
            fname = os.path.basename(image_path)
            bt.setShowingPicture(fname)
            print(f"Uploaded and set image: {fname}")
        else:
            print(f"Warning: Image file '{image_path}' not found, skipping")
    
    # Apply solid colors if specified
    if 'solid_colors' in config:
        for color_config in config['solid_colors']:
            color = color_config.get('color', '000000')
            leds = color_config.get('leds', ['ALL'])
            dim = color_config.get('dim', 1.0)
            reset = color_config.get('reset', True)
            
            # Convert leds to BusyTag.LEDS enum
            led_list = []
            for i in leds:
                if isinstance(i, str):
                    if i.lower() == 'all':
                        led_list = [BusyTag.LEDS.ALL]
                        break
                    led_list.append(BusyTag.LEDS[i.upper()])
                if isinstance(i, int):
                    led_list.append(i)
            
            bt.setSolidColor(color, scale=dim, leds=led_list, clear=reset)
            print(f"Set solid color {color} on LEDs {leds} (dim: {dim}, reset: {reset})")
    
    # Apply pattern(s) if specified
    if 'pattern' in config:
        pattern_names = config['pattern']
        repeat = config.get('repeat', 255)
        
        # Handle both single pattern (string) and multiple patterns (list)
        if isinstance(pattern_names, str):
            pattern_names = [pattern_names]
        
        # Merge all patterns into a single list
        merged_patterns = []
        for pattern_name in pattern_names:
            # Check if it's a custom pattern definition
            if isinstance(pattern_name, dict):
                # Parse custom pattern definition
                custom_pattern = pattern_name
                leds = custom_pattern.get('leds', ['ALL'])
                color = custom_pattern.get('color', 'FFFFFF')
                speed = custom_pattern.get('speed', 100)
                delay = custom_pattern.get('delay', 0)
                dim = custom_pattern.get('dim', 1.0)
                
                # Convert leds to BusyTag.LEDS enum
                led_list = []
                for i in leds:
                    if isinstance(i, str):
                        if i.lower() == 'all':
                            led_list = [BusyTag.LEDS.ALL]
                            break
                        led_list.append(BusyTag.LEDS[i.upper()])
                    if isinstance(i, int):
                        led_list.append(i)
                
                # Create BusyTagPattern object
                pattern_obj = BusyTagPattern(
                    leds=led_list,
                    color=color,
                    scale=dim,
                    speed=speed,
                    delay=delay
                )
                merged_patterns.append(pattern_obj)
                print(f"Added custom pattern: color={color}, leds={leds}, speed={speed}, delay={delay}")
            else:
                # Use default pattern
                try:
                    pattern = BusyTagDefaultPattern[pattern_name.upper()]
                    merged_patterns.extend(pattern.value)
                    print(f"Added pattern '{pattern_name}'")
                except KeyError as e:
                    print(f"Error: Unknown pattern '{pattern_name}'")
                    print("Available patterns:")
                    for p in BusyTagDefaultPattern:
                        print(f"  - {p.name}")
                    sys.exit(1)
        
        # Set the merged pattern
        if merged_patterns:
            bt.setCustomPattern(merged_patterns, repeat)
            print(f"Set {len(pattern_names)} pattern(s) with repeat: {repeat}")
    
    print("Configuration applied successfully!")

def uri_command(args, bt):
    uri = urlparse(args.uri)

    if uri.scheme != "busytag":
        print("Wrong URI scheme. Required URI like busytag://...")
        return
    
    qs =  parse_qs(uri.query)

    filename = os.path.basename(uri.path)
    color = qs.get("color", ["blue"])[0].replace("#", "").lower()
    pattern_str = qs.get("pattern", [None])[0]
    pattern_repeat = qs.get("repeat", [255])[0]
    pattern = None

    if pattern_str:
        pattern = BusyTagDefaultPattern[pattern_str.upper()].value
    
    # ParseResult(
    #     scheme='busytag',
    #     netloc='igapi.busy-tag.com',
    #     path='/uploads/5d/5d6685e996b62d6cc2d3159c99627f6cc598a26833d35636571e41cb6fbc6ce1.png',
    #     params='',
    #     query='color=%23FFA500&original_ext=.png',
    #     fragment=''
    # )
    if len(filename) > 25:
        filename = filename[-25:]

    bt.mount()
    bt.putFileFromUrl(url=f"https://{uri.netloc}{uri.path}", filename=filename)    
    bt.setShowingPicture(filename)
    bt.setSolidColor(color=color, clear=True)
    if pattern:
        bt.setCustomPattern(pattern, repeat=pattern_repeat)
    else:
        bt.playPattern(False)

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--device", type=str, required=True)
    parser.add_argument("--json", action="store_true")

    subparsers = parser.add_subparsers(dest="command")

    # Show
    show = subparsers.add_parser('show', help="Show Information")
    show.set_defaults(func=show_command)

    # Pictures
    pictures = subparsers.add_parser('pictures', help="Interact with Pictures")
    pictures.set_defaults(func=picture_command)
    pictures_subparsers = pictures.add_subparsers(dest="pcommand")
    
    # list picture
    pictures_list = pictures_subparsers.add_parser("list", help="List Pictures")
    # upload picture
    picture_upload = pictures_subparsers.add_parser("upload", help="Upload Picture")
    picture_upload.add_argument("filename", help="Path to file for upload")
    picture_upload.add_argument("--use", action="store_true", default=True, help="Set Picture as Background")
    # display picture
    picture_display = pictures_subparsers.add_parser("display", help="Display Picture")
    picture_display.add_argument("filename", help="File to display")
    # delete picture
    picture_display = pictures_subparsers.add_parser("delete", help="Delete Picture")
    picture_display.add_argument("filename", help="File to delete")

    # LED
    led = subparsers.add_parser('led', help="Interact with LEDs")
    led.set_defaults(func=led_command)
    led_subparsers = led.add_subparsers(dest="lcommand")
    
    # LED on
    led_on = led_subparsers.add_parser("on", help="Set LEDs On")
    led_on.add_argument("color", type=str, default="000000", help="Color Value")
    led_on.add_argument("--dim", type=float, default="1.0", help="LED brightness 0.0 - 1.0 (Default: 1.0)")
    led_on.add_argument("--reset", action="store_true", default=False, help="Reset all LEDs befor setting color (Default: False)")
    led_on.add_argument("--led", choices=["all", "0", "1", "2", "3", "4", "5", "6"], default=["all"], nargs="+", help="LEDs to set (Default: all)")

    # LED off
    led_off = led_subparsers.add_parser("off", help="Set LEDs Off")

    # LED PATTERN
    led_pattern = subparsers.add_parser('led-pattern', help="Interact with LED Patterns")
    led_pattern.set_defaults(func=led_pattern_command)
    led_pattern_subparsers = led_pattern.add_subparsers(dest="lpcommand")

    led_pattern_on = led_pattern_subparsers.add_parser("on", help="Set LED Pattern")
    led_pattern_on.add_argument("pattern", type=str, default="DEFAULT", help="Pattern Name")
    led_pattern_on.add_argument("--repeat", type=int, default=255, help="Repeat Pattern n times")

    led_pattern_off = led_pattern_subparsers.add_parser("off", help="Stop LED Pattern")

    # RAW
    raw = subparsers.add_parser('raw', help="Send raw command")
    raw.add_argument("command", type=str, help="Command to send")
    raw.set_defaults(func=raw_command)

    # CONFIG
    preset = subparsers.add_parser('preset', help="Apply preset configuration from file")
    preset.add_argument("preset_file", type=str, help="Path to preset configuration file")
    preset.set_defaults(func=preset_command)

    # URI Handler
    # see https://ig.busy-tag.com/ig/
    uri = subparsers.add_parser('uri', help="Busytag URI Handler")
    uri.add_argument("uri", type=str, help="Busytag URI")
    uri.set_defaults(func=uri_command)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit()

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG if args.debug else logging.INFO)

    bt = BusyTag(args.device)

    args.func(args, bt)


if __name__ == "__main__":
    main()