#!/bin/bash
set -euo pipefail

SCREENSHOT_FILENAME=$(date +'%Y-%m-%dT%H:%M:%S%z_grim.png')
SCREENSHOT_FILENAME_ABSOLUTE=$HOME/Pictures/Screenshots/$SCREENSHOT_FILENAME

notify-send --app-name=grim --urgency=normal --category=screenshot "Capturing entire screen to $SCREENSHOT_FILENAME_ABSOLUTE"
grim $SCREENSHOT_FILENAME_ABSOLUTE
ksnip $SCREENSHOT_FILENAME_ABSOLUTE

# play $HOME/.config/hypr/assets/sounds/camera-shutter.ogg

