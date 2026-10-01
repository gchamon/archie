#!/bin/bash
set -euo pipefail

df_command="${DF_COMMAND:-df}"
df_output="$("$df_command" --local -h --output=fstype,size,used,pcent,target -x tmpfs -x devtmpfs -x efivarfs)" || {
    printf 'Unable to read filesystem usage with %s\n' "$df_command" >&2
    exit 1
}

tooltip_rows="$(printf '%s\n' "$df_output" | awk '
    NR == 1 { next }
    NF >= 5 {
        filesystem_type = $1
        size = $2
        used = $3
        percentage = $4
        mount = $NF
        if (filesystem_type != "" && size != "" && used != "" && percentage ~ /^[0-9]+%$/ && mount != "") {
            count++
            mounts[count] = mount
            capacities[count] = used " / " size
            percentages[count] = percentage
            if (length(mount) > mount_width) mount_width = length(mount)
            if (length(capacities[count]) > capacity_width) capacity_width = length(capacities[count])
            if (length(percentage) > percentage_width) percentage_width = length(percentage)
            if (mount == "/") root_percentage = percentage
        }
    }
    END {
        if (count == 0 || root_percentage == "") exit 1
        for (i = 1; i <= count; i++) {
            printf "%-*s  %*s  %*s%s", mount_width, mounts[i], capacity_width, capacities[i], percentage_width, percentages[i], i < count ? "\n" : ""
        }
    }
')" || {
    printf 'No root filesystem usage found in df output\n' >&2
    exit 1
}

root_percentage="$(printf '%s\n' "$df_output" | awk 'NR > 1 && $NF == "/" { gsub(/%/, "", $4); print $4; exit }')"
tooltip="Disk usage"$'\n'"$tooltip_rows"
jq -cn \
    --arg text "${root_percentage}%" \
    --arg tooltip "$tooltip" \
    '{text: $text, tooltip: $tooltip, class: "disk"}'
