#!/bin/bash

# grimblast [--notify] [--cursor] [--freeze] [--wait N] [--scale <scale>] (copy|save|copysave|edit) [active|screen|output|area] [FILE|-]
export GRIMBLAST_EDITOR=ksnip

if pgrep ksnip; then
    pkill ksnip
    sleep 1
fi
grimblast edit area
