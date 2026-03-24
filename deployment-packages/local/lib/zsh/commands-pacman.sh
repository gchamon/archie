#!/usr/bin/env zsh

alias pacmatic='sudo --preserve-env=pacman_program /usr/bin/pacmatic'

_pkg:require-arg() {
  local cmd_name="${funcstack[2]:-$0}"

  if [[ -z "$1" ]]; then
    echo "Usage: ${cmd_name} <package-or-search-term>" >&2
    return 1
  fi
}

autoremove() {
  PKGS=$(yay -Qdtq)
  yay -Rcns $PKGS
}

pacman:installed() {
  pacman -Qq "$@"
}

pacman:manual() {
  pacman -Qqe "$@"
}

pacman:deps() {
  pacman -Qqd "$@"
}

pacman:orphans() {
  pacman -Qdtq "$@"
}

pacman:foreign() {
  pacman -Qmq "$@"
}

pacman:search() {
  _pkg:require-arg "$1" || return 1
  pacman -Ss "$@"
}

pacman:info() {
  _pkg:require-arg "$1" || return 1

  if pacman -Qq "$1" >/dev/null 2>&1; then
    pacman -Qi "$@"
  else
    pacman -Si "$@"
  fi
}

pacman:files() {
  _pkg:require-arg "$1" || return 1
  pacman -Fl "$@"
}

pacman:owns() {
  _pkg:require-arg "$1" || return 1
  pacman -Qo "$@"
}

pacman:install() {
  _pkg:require-arg "$1" || return 1
  sudo pacman -S "$@"
}

pacman:remove() {
  _pkg:require-arg "$1" || return 1
  sudo pacman -R "$@"
}

pacman:remove-deps() {
  _pkg:require-arg "$1" || return 1
  sudo pacman -Rns "$@"
}

pacman:update() {
  sudo pacman -Syu "$@"
}

pacman:refresh() {
  sudo pacman -Sy "$@"
}

pacman:clean() {
  sudo pacman -Sc "$@"
}

pacman:clean-all() {
  sudo pacman -Scc "$@"
}

yay:installed() {
  yay -Qq "$@"
}

yay:search() {
  _pkg:require-arg "$1" || return 1
  yay -Ss "$@"
}

yay:info() {
  _pkg:require-arg "$1" || return 1
  yay -Si "$@"
}

yay:install() {
  _pkg:require-arg "$1" || return 1
  yay -S "$@"
}

yay:remove() {
  _pkg:require-arg "$1" || return 1
  yay -R "$@"
}

yay:update() {
  yay -Syu "$@"
}

yay:clean() {
  yay -Sc "$@"
}

yay:orphans() {
  local pkgs
  pkgs=("${(@f)$(pacman -Qdtq 2>/dev/null)}")

  if (( ${#pkgs[@]} == 0 )); then
    echo "No orphan packages found."
    return 0
  fi

  printf '%s\n' "${pkgs[@]}"
}

yay:purge-orphans() {
  local pkgs
  pkgs=("${(@f)$(pacman -Qdtq 2>/dev/null)}")

  if (( ${#pkgs[@]} == 0 )); then
    echo "No orphan packages found."
    return 0
  fi

  yay -Rcns "${pkgs[@]}"
}
