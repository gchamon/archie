#!/bin/bash
set -euo pipefail
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

EXIT_TYPE="${1:?err}"

calculate_width() {
    type_length="${#1}"

    # this formula is empirical
    # takes the ceil of division by 2 of the length of the type string and adds to 11
    # the result is the percentage of the maximum width the window has to occupy
    # exit = 13%; reboot = 14%; poweroff = 15%;
    # other modes will scale accordingly
    width=$((11+($type_length+1)/2))%
    echo $width
}

if [[ "$EXIT_TYPE" == "exit" ]]; then
    EXIT_ACTION="$SCRIPT_DIR"/force-exit.sh
elif [[ "$EXIT_TYPE" == "poweroff" ]]; then
    EXIT_ACTION="sudo poweroff"
elif [[ "$EXIT_TYPE" == "reboot" ]]; then
    EXIT_ACTION="sudo reboot"
else
    echo "Action unsupported: $EXIT_TYPE"
    notify-send "Action unsupported: $EXIT_TYPE"
    exit 1
fi

if [[ "$(rofi -dmenu -p "Confirm $EXIT_TYPE? [y/N]" -theme-str "listview { enabled: false; } window { width: $(calculate_width $EXIT_TYPE); }" | awk '{print tolower($0)}' )" == "y" ]]; then
    bash -c "$EXIT_ACTION"
fi
