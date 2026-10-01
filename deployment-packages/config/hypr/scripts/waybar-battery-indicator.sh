#!/bin/bash
set -euo pipefail

upower_command="${UPOWER_COMMAND:-upower}"
uptime_command="${UPTIME_COMMAND:-uptime}"
who_command="${WHO_COMMAND:-who}"
devices="$("$upower_command" -e)"
battery="$(printf '%s\n' "$devices" | awk '/\/battery_[^[:space:]]+/ { print; exit }')"
if [[ -z "$battery" ]]; then
    printf 'No UPower battery device found\n' >&2
    exit 1
fi

battery_info="$("$upower_command" -i "$battery")"
uptime_report="$("$uptime_command" -p)"
uptime_text="${uptime_report#up }"
uptime_days="$(printf '%s\n' "$uptime_report" | awk '{
    seconds = 0
    for (i = 1; i < NF; i++) {
        amount = $i
        gsub(/[^0-9]/, "", amount)
        if (amount == "") {
            continue
        }
        unit = $(i + 1)
        if (unit ~ /^week/) {
            seconds += amount * 604800
        } else if (unit ~ /^day/) {
            seconds += amount * 86400
        } else if (unit ~ /^hour/) {
            seconds += amount * 3600
        } else if (unit ~ /^minute/) {
            seconds += amount * 60
        } else if (unit ~ /^second/) {
            seconds += amount
        }
    }
    printf "%d", int(seconds / 86400 + 0.5)
}')"
if (( uptime_days == 1 )); then
    uptime_days_label="day"
else
    uptime_days_label="days"
fi
percentage="$(printf '%s\n' "$battery_info" | awk -F: '$1 ~ /^[[:space:]]*percentage[[:space:]]*$/ { gsub(/[[:space:]]/, "", $2); print $2; exit }')"
state="$(printf '%s\n' "$battery_info" | awk -F: '$1 ~ /^[[:space:]]*state[[:space:]]*$/ { sub(/^[[:space:]]*/, "", $2); print $2; exit }')"
health="$(printf '%s\n' "$battery_info" | awk -F: '$1 ~ /^[[:space:]]*capacity[[:space:]]*$/ { sub(/^[[:space:]]*/, "", $2); print $2; exit }')"
cycles="$(printf '%s\n' "$battery_info" | awk -F: '$1 ~ /^[[:space:]]*charge-cycles[[:space:]]*$/ { sub(/^[[:space:]]*/, "", $2); print $2; exit }')"
runtime="$(printf '%s\n' "$battery_info" | awk -F: '$1 ~ /^[[:space:]]*time to empty[[:space:]]*$/ { sub(/^[[:space:]]*/, "", $2); print $2; exit }')"
time_to_full="$(printf '%s\n' "$battery_info" | awk -F: '$1 ~ /^[[:space:]]*time to full[[:space:]]*$/ { sub(/^[[:space:]]*/, "", $2); print $2; exit }')"
line_power="$(printf '%s\n' "$devices" | awk '/\/line_power_[^[:space:]]+/ { print; exit }')"
line_power_online="no"
if [[ "$state" != "charging" && -n "$line_power" ]]; then
    line_power_info="$("$upower_command" -i "$line_power" 2>/dev/null || true)"
    line_power_online="$(printf '%s\n' "$line_power_info" | awk -F: '$1 ~ /^[[:space:]]*online[[:space:]]*$/ { sub(/^[[:space:]]*/, "", $2); print $2; exit }')"
fi
if [[ ! "$percentage" =~ ^[0-9]+%$ || -z "$state" || -z "$uptime_text" ]]; then
    printf 'Unable to read required battery status\n' >&2
    exit 1
fi
health="${health:-unavailable}"
cycles="${cycles:-unavailable}"
if [[ "$state" == "charging" || "$line_power_online" == "yes" ]]; then
    runtime="—"
else
    runtime="${runtime:-unavailable}"
fi
reboot="$("$who_command" -b 2>/dev/null | awk '{ $1 = ""; $2 = ""; sub(/^[[:space:]]+/, ""); print; exit }' || true)"
reboot="${reboot:-unavailable}"
capacity="${percentage%%%}"

if [[ "$state" == "charging" ]]; then
    icon="󰂄"
elif (( capacity < 20 )); then
    icon=""
elif (( capacity < 40 )); then
    icon=""
elif (( capacity < 60 )); then
    icon=""
elif (( capacity < 80 )); then
    icon=""
else
    icon=""
fi
if (( capacity < 15 )); then
    class="critical"
elif (( capacity < 30 )); then
    class="warning"
else
    class="battery"
fi
tooltip="Battery"
add_tooltip_row() {
    printf -v tooltip '%s\n%-20s %s' "$tooltip" "$1" "$2"
}
if [[ "$state" == "charging" ]]; then
    add_tooltip_row "Charge:" "${percentage} (charging; TTF: ${time_to_full:-unavailable})"
else
    add_tooltip_row "Charge:" "${percentage} (${state})"
fi
add_tooltip_row "Estimated runtime:" "$runtime"
add_tooltip_row "Health:" "$health"
add_tooltip_row "Charge cycles:" "$cycles"
add_tooltip_row "Uptime:" "$uptime_text"
add_tooltip_row "Last reboot:" "${reboot} (${uptime_days} ${uptime_days_label} ago)"
jq -cn --arg text "${icon} ${percentage}" --arg tooltip "$tooltip" --arg class "$class" '{text: $text, tooltip: $tooltip, class: $class}'
