#!/bin/bash
set -euo pipefail
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

EXIT_TYPE="${1:?err}"

EXIT_ACTION=$({
    if [[ "$EXIT_TYPE" == "exit" ]]; then
        echo "$SCRIPT_DIR"/force-exit.sh
    elif [[ "$EXIT_TYPE" == "poweroff" ]]; then
        echo sudo poweroff
    elif [[ "$EXIT_TYPE" == "reboot" ]]; then
        echo sudo reboot
    else
        echo "Action unsupported: $EXIT_TYPE"
        notify-send "Action unsupported: $EXIT_TYPE"
        exit 1
    fi
})

if [[ "$(rofi -dmenu -p "Confirm $EXIT_TYPE? [y/N]" -theme-str 'listview { enabled: false; } window { width: 10%; } ' | awk '{print tolower($0)}' )" == "y" ]]; then
    bash -c "$EXIT_ACTION"
fi
