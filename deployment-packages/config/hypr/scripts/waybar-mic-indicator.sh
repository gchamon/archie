#!/bin/bash
# waybar-mic-indicator.sh
# Emit "MIC" when an application captures audio from an unmuted microphone.
# Used by Waybar custom/mic modules.
#
# Runtime dependency: pactl (PipeWire PulseAudio compatibility layer).

set -euo pipefail

if [[ -z "$(pactl list source-outputs short)" ]]; then
    exit 0
fi

default_source=$(pactl get-default-source)
if [[ "$(pactl get-source-mute "$default_source")" == "Mute: yes" ]]; then
    exit 0
fi

printf 'MIC\n'
