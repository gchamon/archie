#!/bin/bash
set -euo pipefail

# this adds frequency sorted history to rofi -dmenu

if [[ -z "$1" ]]; then
    echo Usage ./launch-rofi-frece.sh {ROFI_TYPE}
    echo Rofi type can be anything describing the rofi usage, for instance shell or terminal
fi

ROFI_TYPE="$1"
DB_FILE="$HOME/.cache/rofi.$ROFI_TYPE.db"
if ! [[ -f "$DB_FILE" ]]; then
    frece init "$DB_FILE" /dev/null
fi

item=$(frece print "$DB_FILE" | rofi "$@" -dmenu -p $ROFI_TYPE)
[[ -z $item ]] && exit 1

if ! frece increment "$DB_FILE" "$item" >/dev/null 2>&1; then
    frece add "$DB_FILE" "$item"
fi

echo "$item"
