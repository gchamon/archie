#!/usr/bin/env zsh

[ "$TERM" = "xterm-kitty" ] && alias sshk="kitty +kitten ssh "

alias sudo="sudo "
alias vim="$VIM_BIN "
alias where='new_where '
alias icat="kitten icat "

alias l='ls -l'
alias la='ls -a'
alias lla='ls -la'
alias ls='lsd '
alias lsh="l -sHi"
alias lt='ls --tree'
alias ltb='lt | bat'

new_where() {
  ll $(which $1)
}

rgx() {
  echo $1 | rg -e $2
}

clear_scrollback() {
  printf '\033[2J\033[3J\033[1;1H'
}

psgrep() {
  ps -ax | grep $1 | grep -v grep
}
