#!/bin/bash
set -euo pipefail
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

EXIT_TYPE="${1:?exit type missing}"

calculate_width() {
    type_length="${#1}"

    # make base width depend on the active monitor width
    # base width is a linear equation that maps 1920p to 11 base width and 4k to 3 base width, more or less
    active_monitor_width=$(hyprctl -j monitors | jq ".[] | select(.id == $(hyprctl -j activeworkspace | jq -r .monitorID)) | .width")
    base_width=$(bc <<< "$active_monitor_width*-0.004+20" | awk '{print int($1+0.5)}')

    # this formula is empirical
    # takes the ceil of division by 2 of the length of the type string and adds to base_width
    # the result is the percentage of the maximum width the window has to occupy
    # exit = 13%; reboot = 14%; poweroff = 15%;
    # other modes will scale accordingly
    width=$(($base_width+($type_length+1)/2))%
    echo $width
}

if [[ "$EXIT_TYPE" == "exit" ]]; then
    EXIT_ACTION="$SCRIPT_DIR"/force-exit.sh
elif [[ "$EXIT_TYPE" == "poweroff" ]]; then
    EXIT_ACTION="poweroff"
elif [[ "$EXIT_TYPE" == "reboot" ]]; then
    EXIT_ACTION="reboot"
else
    echo "Action unsupported: $EXIT_TYPE"
    notify-send "Action unsupported: $EXIT_TYPE"
    exit 1
fi

calculated_width=$(calculate_width $EXIT_TYPE)
echo $calculated_width
if [[ "$(rofi -dmenu -p "Confirm $EXIT_TYPE? [y/N]" -theme-str "listview { enabled: false; } window { width: $calculated_width; }" | awk '{print tolower($0)}' )" == "y" ]]; then
    # this is necessary so that chrome preserves its internal session and I can join zoom calls without having to re-login. Thanks zoom.
    notify-send "$EXIT_TYPE: killing chrome"
    pkill -KILL chromium || true
    bash -c "$EXIT_ACTION"
fi
