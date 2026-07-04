#!/bin/bash
# waybar-share-indicator.sh
# Emit "SHARE" when xdg-desktop-portal-hyprland has an active screen capture
# stream.  Used by Waybar custom/share module.
#
# Runtime dependencies: pw-dump (pipewire-cli), jq

set -euo pipefail

pw-dump | jq -r '
  map(.info?.props?)
  | map(select(
      .["node.name"]? == "xdg-desktop-portal-hyprland"
    ))
  | if length > 0 then "SHARE" else empty end
'
