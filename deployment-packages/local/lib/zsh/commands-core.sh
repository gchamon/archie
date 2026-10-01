#!/usr/bin/env zsh

[ "$TERM" = "xterm-kitty" ] && alias sshk='kitty +kitten ssh'

alias sudo='sudo '
alias vim="${VIM_BIN:-/usr/bin/vim}"
alias where='new_where'
alias icat='kitten icat'
alias t='tee'
alias trim='xargs -n1 echo'

alias l='ls -l'
alias la='ls -a'
alias lla='ls -la'
alias ls='lsd'
alias lsh='l -sHi'
alias lt='ls --tree'
alias ltb='lt | bat'

alias kitten:emoji='kitten unicode-input | wl-copy'

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

headtail() {
  local head=10 tail=10
  while (( $# )); do
    case $1 in
      -n|-h|-t)
        if (( $# < 2 )) || [[ ! $2 == <-> ]] || (( $2 < 1 )); then
          print -u2 "usage: headtail [-n count] [-h count] [-t count]"
          return 2
        fi
        case $1 in
          -n) head=$2; tail=$2 ;;
          -h) head=$2 ;;
          -t) tail=$2 ;;
        esac
        shift 2
        ;;
      *)
        print -u2 "usage: headtail [-n count] [-h count] [-t count]"
        return 2
        ;;
    esac
  done
  awk -v head="$head" -v tail="$tail" '
    { lines[NR % tail] = $0 }
    NR <= head { print }
    END {
      start = NR - tail + 1
      if (start < head + 1) start = head + 1
      for (i = start; i <= NR; i++) print lines[i % tail]
    }
  '
}
