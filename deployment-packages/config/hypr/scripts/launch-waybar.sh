#!/bin/bash

set -euo pipefail

WAYBAR_CONFIG="/var/lib/archie/waybar/config"
WAYBAR_STYLE="/var/lib/archie/waybar/style.css"

trap "killall waybar" EXIT

while true; do
    waybar --config "$WAYBAR_CONFIG" --style "$WAYBAR_STYLE" &
    inotifywait -e create,modify "$WAYBAR_CONFIG" "$WAYBAR_STYLE"
    killall waybar
done
