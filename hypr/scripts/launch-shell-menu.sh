#!/bin/bash
set -euo pipefail

mkdir -p /tmp/rofi-shell-logs

execution_id=$(uuidgen)
cmd_to_execute=$(~/.config/hypr/scripts/launch-rofi-frece.sh shell)

echo "$execution_id $cmd_to_execute" >> /tmp/rofi-shell-logs/index

exec > >(tee /tmp/rofi-shell-logs/"$execution_id".log) 2>&1

echo running ["$cmd_to_execute"]...
bash -c "$cmd_to_execute"
echo finish exeuction

