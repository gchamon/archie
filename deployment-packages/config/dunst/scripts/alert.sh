#!/bin/bash
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
STORE_DATABASE_PATH="/var/lib/archie/store.sqlite3"
CUSTOM_SOUND_PATH="/var/lib/archie/notification-sound"

if [[ "$(/usr/bin/dunstctl is-paused 2>/dev/null)" == "true" ]]; then
    exit 0
fi

sounds_enabled="$(
    /usr/bin/sqlite3 -readonly -cmd ".timeout 2000" "$STORE_DATABASE_PATH" \
        "SELECT value FROM policy WHERE key = 'notifications.sounds.enabled';" \
        2>/dev/null || true
)"
if [[ "$sounds_enabled" == "off" ]]; then
    exit 0
fi

# Warm up audio device in case of powersave policies (like Bluetooth).
/usr/bin/pw-play "$SCRIPT_DIR/../assets/500-milliseconds-of-silence.mp3"
sound_path="$SCRIPT_DIR/../assets/link.mp3"
sound_source="$(
    /usr/bin/sqlite3 -readonly -cmd ".timeout 2000" "$STORE_DATABASE_PATH" \
        "SELECT value FROM policy WHERE key = 'notifications.sound.source';" \
        2>/dev/null || true
)"
if [[ -n "$sound_source" && "$sound_source" != "default" && -r "$CUSTOM_SOUND_PATH" ]]; then
    sound_path="$CUSTOM_SOUND_PATH"
fi
/usr/bin/pw-play "$sound_path"
