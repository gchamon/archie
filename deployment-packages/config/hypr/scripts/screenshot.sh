#!/bin/bash
set -euo pipefail

TARGET="${1:-screen}"
ACTION="${2:-save}"

TARGET_DIR="$HOME/Pictures/Screenshots"
mkdir -p "$TARGET_DIR"

FILENAME="$(date +'%Y-%m-%dT%H:%M:%S%z_grim.png')"
FILEPATH="$TARGET_DIR/$FILENAME"

case "$TARGET" in
    screen)
        grim "$FILEPATH"
        ;;
    area)
        geom="$(slurp)" || exit 0
        grim -g "$geom" "$FILEPATH"
        ;;
    *)
        echo "Usage: $0 [screen|area] [save|ksnip]" >&2
        exit 1
        ;;
esac

case "$ACTION" in
    save)
        notify-send \
            --app-name=grim \
            --urgency=normal \
            --category=screenshot \
            --icon="$FILEPATH" \
            "Screenshot saved" \
            "$FILEPATH"
        ;;
    ksnip)
        ksnip "$FILEPATH" &
        ;;
    *)
        echo "Usage: $0 [screen|area] [save|ksnip]" >&2
        exit 1
        ;;
esac
