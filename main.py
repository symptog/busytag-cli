#!/bin/env python3
# SPDX-License-Identifier: MIT

import json
import time
import serial
import serial.tools.list_ports
import sys
import os

import logging
logger = logging.getLogger(__name__)

from busytag import BusyTag, BusyTagPattern, BusyTagDefaultPattern
 
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
        bt.putFile(args.filename)
        fname = os.path.basename(filename)
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
    try:
        pattern = BusyTagDefaultPattern[args.pattern.upper()]
        bt.setCustomPattern(pattern.value, args.repeat)
    except KeyError as e:
        print("Available Pattern:")
        for p in BusyTagDefaultPattern:
            print(p.name)
    
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
    led_pattern.add_argument("pattern", type=str, default="DEFAULT", help="Pattern Name")
    led_pattern.add_argument("--repeat", type=int, default=255, help="Repeat Pattern n times")
    led_pattern.set_defaults(func=led_pattern_command)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit()

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG if args.debug else logging.INFO)

    bt = BusyTag(args.device)

    args.func(args, bt)


if __name__ == "__main__":
    main()