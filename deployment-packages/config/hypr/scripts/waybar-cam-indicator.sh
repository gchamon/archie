#!/bin/bash
# waybar-cam-indicator.sh
# Emit "CAM" when a physical V4L2 webcam device is open by a process.
# Used by Waybar custom/cam module.
#
# Browsers may open /dev/video* directly instead of creating PipeWire links to
# the camera node, so the active signal is device usage rather than graph links.
#
# Runtime dependencies: pw-dump (pipewire-cli), jq, fuser (psmisc)

set -euo pipefail

while IFS= read -r camera_path; do
    [[ -e "$camera_path" ]] || continue

    if fuser -s "$camera_path"; then
        printf 'CAM\n'
        exit 0
    fi
done < <(
    pw-dump | jq -r '
      .[]
      | select(
          .type == "PipeWire:Interface:Node"
          and .info?.props?["media.class"]? == "Video/Source"
          and .info.props["device.api"]? == "v4l2"
          and .info.props["object.path"]? != null
        )
      | .info.props["object.path"]
      | sub("^v4l2:"; "")
    '
)
