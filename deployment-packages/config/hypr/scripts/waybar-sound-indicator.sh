#!/bin/bash
set -euo pipefail

pactl_command="${PACTL_COMMAND:-pactl}"
default_sink="$("$pactl_command" get-default-sink)"
is_bluetooth_sink=false
[[ "$default_sink" == bluez_output.* ]] && is_bluetooth_sink=true
default_source="$("$pactl_command" get-default-source)"
sinks="$("$pactl_command" list sinks)"
sources="$("$pactl_command" list sources)"

truncate_middle() {
    local name="$1"
    if (( ${#name} > 25 )); then
        printf '%s…%s' "${name:0:12}" "${name: -12}"
    else
        printf '%s' "$name"
    fi
}

parse_device() {
    local device_name="$1"
    local inventory="$2"

    printf '%s\n' "$inventory" | awk -v wanted="$device_name" '
        function finish() {
            if (found && !printed && description != "" && volume != "" && mute != "") {
                printf "%s\t%s\t%s", description, volume, mute
                printed = 1
            }
        }
        /^Sink #[0-9]+/ || /^Source #[0-9]+/ {
            finish()
            in_device = 0
            found = 0
            description = ""
            volume = ""
            mute = ""
        }
        $1 == "Name:" {
            in_device = ($2 == wanted)
            if (in_device) found = 1
        }
        in_device && /^[[:space:]]*Description:/ {
            sub(/^[^:]*:[[:space:]]*/, "")
            description = $0
        }
        in_device && /^[[:space:]]*Volume:/ && volume == "" {
            if (match($0, /[0-9]+%/)) volume = substr($0, RSTART, RLENGTH - 1)
        }
        in_device && /^[[:space:]]*Mute:/ { mute = $2 }
        END { finish() }
    '
}

sink_info="$(parse_device "$default_sink" "$sinks")"
source_info="$(parse_device "$default_source" "$sources")"
if [[ -z "$sink_info" || -z "$source_info" ]]; then
    printf 'Unable to read default audio device state\n' >&2
    exit 1
fi

IFS=$'\t' read -r sink_description sink_volume sink_mute <<<"$sink_info"
IFS=$'\t' read -r source_description source_volume source_mute <<<"$source_info"
if [[ ! "$sink_volume" =~ ^[0-9]+$ || ! "$source_volume" =~ ^[0-9]+$ || ( "$sink_mute" != yes && "$sink_mute" != no ) || ( "$source_mute" != yes && "$source_mute" != no ) ]]; then
    printf 'Invalid default audio device state\n' >&2
    exit 1
fi
sink_description="$(truncate_middle "$sink_description")"
source_description="$(truncate_middle "$source_description")"

if [[ "$sink_mute" == yes ]]; then
    text="󰝟 Mute"
elif (( sink_volume < 34 )); then
    text=" ${sink_volume}%"
elif (( sink_volume < 67 )); then
    text=" ${sink_volume}%"
else
    text=" ${sink_volume}%"
fi
if [[ "$is_bluetooth_sink" == true ]]; then
    text+=" "
fi
state() {
    [[ "$1" == yes ]] && printf 'muted' || printf 'unmuted'
}
add_tooltip_row() {
    printf -v tooltip '%s\n%-10s %-25s %s' "$tooltip" "$1" "$2" "$3"
}
tooltip="Audio"
add_tooltip_row "Output:" "$sink_description" "${sink_volume}% ($(state "$sink_mute"))"
add_tooltip_row "Input:" "$source_description" "${source_volume}% ($(state "$source_mute"))"

webcam_rows="$(printf '%s\n' "$sources" | awk -v default_source="$default_source" '
    function finish() {
        lowered = tolower(name " " description)
        if (name != "" && name != default_source && name !~ /\.monitor$/ && description != "" && volume != "" && mute != "" && lowered ~ /(webcam|camera)/) {
            printf "%s\t%s\t%s\t%s\n", name, description, volume, mute
        }
    }
    /^Source #[0-9]+/ {
        finish()
        name = ""
        description = ""
        volume = ""
        mute = ""
    }
    $1 == "Name:" { name = $2 }
    /^[[:space:]]*Description:/ { sub(/^[^:]*:[[:space:]]*/, ""); description = $0 }
    /^[[:space:]]*Volume:/ && volume == "" { if (match($0, /[0-9]+%/)) volume = substr($0, RSTART, RLENGTH - 1) }
    /^[[:space:]]*Mute:/ { mute = $2 }
    END { finish() }
')"
if [[ -n "$webcam_rows" ]]; then
    while IFS=$'\t' read -r _webcam_name webcam_description webcam_volume webcam_mute; do
        webcam_description="$(truncate_middle "$webcam_description")"
        add_tooltip_row "Webcam:" "$webcam_description" "${webcam_volume}% ($(state "$webcam_mute"))"
    done <<<"$webcam_rows"
fi

jq -cn --arg text "$text" --arg tooltip "$tooltip" '{text: $text, tooltip: $tooltip, class: "sound"}'
