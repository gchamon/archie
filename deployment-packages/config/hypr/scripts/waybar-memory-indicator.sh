#!/bin/bash
set -euo pipefail

# Set MEMINFO_PATH only to inject a fixture in tests; production uses /proc/meminfo.
meminfo_path="${MEMINFO_PATH:-/proc/meminfo}"
read -r total_kib available_kib < <(
    awk '
        $1 == "MemTotal:" { total = $2 }
        $1 == "MemAvailable:" { available = $2 }
        END {
            if (total <= 0 || available < 0) {
                exit 1
            }
            print total, available
        }
    ' "$meminfo_path"
) || {
    printf 'Unable to read total and available memory from %s\n' "$meminfo_path" >&2
    exit 1
}
used_kib=$((total_kib - available_kib))
if (( used_kib < 0 )); then
    used_kib=0
fi
percentage=$(((used_kib * 100 + total_kib / 2) / total_kib))
memory_text="${percentage}%"
memory_ratio="$(awk -v used_kib="$used_kib" -v total_kib="$total_kib" 'BEGIN {
    printf "%.1f/%.1f GiB", used_kib / 1048576, total_kib / 1048576
}')"

processes="$(ps -e -o rss= -o comm=)"
consumers=""
if [[ -n "$processes" ]]; then
    consumers="$(
        printf '%s\n' "$processes" |
            awk '
                {
                    rss = $1
                    name = $0
                    sub(/^[[:space:]]*[0-9]+[[:space:]]*/, "", name)
                    if (rss ~ /^[0-9]+$/ && name != "") {
                        resident_kib[name] += rss
                    }
                }
                END {
                    for (name in resident_kib) {
                        printf "%d\t%s\n", resident_kib[name], name
                    }
                }
            ' |
            sort -nr -k1,1 |
            awk '
                NR <= 5 {
                    resident_kib[NR] = $1
                    name = $0
                    sub(/^[0-9]+[[:space:]]*/, "", name)
                    names[NR] = name
                    count = NR
                    if (length(name) > name_width) {
                        name_width = length(name)
                    }
                    value_width = length(sprintf("%.1f", $1 / 1024))
                    if (value_width > max_value_width) {
                        max_value_width = value_width
                    }
                }
                END {
                    if (count == 0) {
                        print "No processes found"
                        exit
                    }
                    for (i = 1; i <= count; i++) {
                        printf "%-*s  %*.*f MiB%s", \
                            name_width, names[i], max_value_width, 1, \
                            resident_kib[i] / 1024, i < count ? "\n" : ""
                    }
                }
            '
    )"
fi

if [[ -z "$consumers" ]]; then
    consumers="No processes found"
fi
tooltip="$memory_ratio"$'\n'"Top memory consumers"$'\n'"$consumers"

jq -cn \
    --arg text "$memory_text" \
    --arg tooltip "$tooltip" \
    '{text: $text, tooltip: $tooltip, class: "memory"}'
