#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

source "$HOME/.zshenv"

SOUNDS_CONFIG_PATH="${XDG_CONFIG_HOME:-$HOME/.config}/archie/notification-sounds.json"

if [[ "$(dunstctl is-paused 2>/dev/null)" == "true" ]]; then
    exit 0
fi

if [[ -f "$SOUNDS_CONFIG_PATH" ]] && [[ "$(jq -r '.enabled // true' "$SOUNDS_CONFIG_PATH" 2>/dev/null)" == "false" ]]; then
    exit 0
fi

# Warm up audio device in case of powersave policies (like Bluetooth).
pw-play "$SCRIPT_DIR/../assets/500-milliseconds-of-silence.mp3"
sound_path="$SCRIPT_DIR/../assets/link.mp3"
if [[ -f "$SOUNDS_CONFIG_PATH" ]]; then
    configured_sound_path="$(jq -r '.sound_path // empty' "$SOUNDS_CONFIG_PATH" 2>/dev/null)"
    if [[ -n "$configured_sound_path" && -f "$configured_sound_path" && -r "$configured_sound_path" ]]; then
        sound_path="$configured_sound_path"
    fi
fi
pw-play "$sound_path"
