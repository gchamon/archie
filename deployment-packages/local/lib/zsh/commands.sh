#!/usr/bin/env zsh

: "${ZSHLIB:=$HOME/.local/lib/zsh}"

test -f "$ZSHLIB/commands-core.sh" && source "$ZSHLIB/commands-core.sh"
test -f "$ZSHLIB/commands-agents.sh" && source "$ZSHLIB/commands-agents.sh"
test -f "$ZSHLIB/commands-git.sh" && source "$ZSHLIB/commands-git.sh"
test -f "$ZSHLIB/commands-system.sh" && source "$ZSHLIB/commands-system.sh"
test -f "$ZSHLIB/commands-devtools.sh" && source "$ZSHLIB/commands-devtools.sh"
test -f "$ZSHLIB/commands-pacman.sh" && source "$ZSHLIB/commands-pacman.sh"
