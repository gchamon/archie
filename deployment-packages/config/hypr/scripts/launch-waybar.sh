#!/bin/bash

set -euo pipefail

WAYBAR_DIRECTORY="${WAYBAR_DIRECTORY:-/var/lib/archie/waybar}"
WAYBAR_COMMAND="${WAYBAR_COMMAND:-waybar}"
WAYBAR_CONFIG="$WAYBAR_DIRECTORY/config"
WAYBAR_STYLE="$WAYBAR_DIRECTORY/style.css"
waybar_pid=""

stop_waybar() {
    if [[ -n "$waybar_pid" ]]; then
        kill "$waybar_pid" 2>/dev/null || true
        wait "$waybar_pid" 2>/dev/null || true
        waybar_pid=""
    fi
}

trap stop_waybar EXIT INT TERM

while true; do
    "$WAYBAR_COMMAND" --config "$WAYBAR_CONFIG" --style "$WAYBAR_STYLE" &
    waybar_pid="$!"
    inotifywait --quiet --event moved_to --include '.*/style\.css$' "$WAYBAR_DIRECTORY"
    stop_waybar
done
