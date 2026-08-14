#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

source "$HOME/.zshenv"

SOUNDS_CONFIG_PATH="${XDG_CONFIG_HOME:-$HOME/.config}/archie/notification-sounds.json"

if [[ -f "$SOUNDS_CONFIG_PATH" ]] && [[ "$(jq -r '.enabled // true' "$SOUNDS_CONFIG_PATH" 2>/dev/null)" == "false" ]]; then
    exit 0
fi

# Warm up audio device in case of powersave policies (like Bluetooth).
pw-play "$SCRIPT_DIR/../assets/500-milliseconds-of-silence.mp3"
pw-play "$SCRIPT_DIR/../assets/link.mp3"
