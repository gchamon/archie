#!/bin/bash
# waybar-share-indicator.sh
# Emit "SHARE" when xdg-desktop-portal-hyprland has an active screen capture
# stream.  Used by Waybar custom/share module.
#
# Runtime dependencies: archie CLI, pw-dump (pipewire-cli) via Archie.

set -euo pipefail

if [[ "$(archie system get share-state)" == "on" ]]; then
    printf 'SHARE\n'
fi
