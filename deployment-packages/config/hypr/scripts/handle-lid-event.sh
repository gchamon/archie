#!/bin/bash

set -euo pipefail

LOG_FILE=/tmp/handle-lid-event.log
exec >>"$LOG_FILE" 2>&1

echo "[$(date --iso-8601=seconds)] handle-lid-event.sh start: args=$*"
echo "[$(date --iso-8601=seconds)] environment: HYPRLAND_INSTANCE_SIGNATURE=${HYPRLAND_INSTANCE_SIGNATURE:-} WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-} XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-}"

usage() {
    echo "Usage: handle-lid-event.sh close|open" >&2
}

if [[ $# -ne 1 ]]; then
    usage
    exit 2
fi

action="$1"
lid_close_behavior="$(archie system get lid-close-behavior 2>/dev/null || true)"
echo "[$(date --iso-8601=seconds)] action=$action lid_close_behavior=$lid_close_behavior"

if [[ "$lid_close_behavior" == "none" ]]; then
    echo "[$(date --iso-8601=seconds)] lid close behavior is none; leaving session and display state unchanged"
    exit 0
fi

case "$action" in
    close)
        if [[ "$lid_close_behavior" == "hibernate" ]]; then
            echo "[$(date --iso-8601=seconds)] starting hyprlock before hibernate"
            hyprlock &
        elif [[ "$lid_close_behavior" == "lock" ]]; then
            echo "[$(date --iso-8601=seconds)] running hyprctl dispatch dpms off"
            hyprctl dispatch dpms off
        fi
        ;;
    open)
        if [[ "$lid_close_behavior" == "lock" ]]; then
            echo "[$(date --iso-8601=seconds)] running hyprctl dispatch dpms on"
            hyprctl dispatch dpms on
            echo "[$(date --iso-8601=seconds)] starting hyprlock after lid open"
            hyprlock &
        fi
        ;;
    *)
        usage
        exit 2
        ;;
esac

echo "[$(date --iso-8601=seconds)] handle-lid-event.sh done"
