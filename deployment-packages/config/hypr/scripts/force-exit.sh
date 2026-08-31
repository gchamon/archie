#!/bin/bash

echo "Hyprland exit" | systemd-cat -t coffebar -p info
hyprctl dispatch 'hl.dsp.exit()' &
sleep 10
echo "Hyprland failed to exit" | systemd-cat -t coffebar -p err
killall -9 Hyprland
