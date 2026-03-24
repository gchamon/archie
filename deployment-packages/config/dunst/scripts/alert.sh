#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

source "$HOME/.zshenv"

if [[ "$DUNST_QUIET" != "true" ]]; then
    # warm up audio device in case of powersave policies (like bluetooth)
    pw-play $SCRIPT_DIR/../assets/500-milliseconds-of-silence.mp3
    pw-play $SCRIPT_DIR/../assets/link.mp3
fi
