#!/bin/bash

SCREENSHOT_FILENAME=$(date +'%Y-%m-%dT%H:%M:%S%z_grim.png')
SCREENSHOT_FILENAME_ABSOLUTE=$HOME/Pictures/Screenshots/$SCREENSHOT_FILENAME

grimblast save area $SCREENSHOT_FILENAME_ABSOLUTE
sleep 1 && notify-send --app-name=grim --urgency=normal --category=screenshot "Capturing area to $SCREENSHOT_FILENAME_ABSOLUTE"
ksnip -e ~/Pictures/Screenshots/2026-03-24T10:36:16-0300_grim.png
