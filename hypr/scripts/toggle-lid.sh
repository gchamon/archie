#!/bin/bash

source ~/.zshenv

if [[ "$HYPRLAND_DISABLE_LID_CLOSE" != "true" ]]; then
    notify-send "Lid close"
fi
