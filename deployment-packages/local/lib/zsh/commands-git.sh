#!/usr/bin/env zsh

git:checkout-main() {
  gco "$(git_main_branch)"
}

git:difftool-meld() {
  git difftool -t meld -y "$@"
}

git:force-checks() {
  gca! --no-edit && git:push --force
}

git:log-origin-development() {
  gl origin development "$@"
}

git:log-divergence() {
  git log "origin/master..$(git_current_branch)" --oneline --no-merges "$@"
}

git:log-origin-main() {
  gl origin "$(git_main_branch)" "$@"
}

git:push() {
  ggpush "$@"
}

git:prune() {
  git prune -v "$@"
}

git:pull-prune() {
  git pull --prune "$@" && git:prune
}

git:review() {
  if [[ "$(git_current_branch)" != review* ]]; then
    git checkout -b "review/$(git_current_branch)"
  fi

  gpsetup
}

git:reset-origin-hard() {
  git reset "origin/$(git_current_branch)" --hard
}

git:squash() {
  if [[ -z "$1" ]]; then
    echo "You must provide a target branch"
    return -1
  fi

  local CUR_BRANCH="$(git_current_branch)"
  local TARGET_BRANCH="$1"
  git pull
  git commit -a -m "commiting rest of changes before squashing"
  gpsetup
  git checkout "origin/$TARGET_BRANCH"
  git checkout -b "$CUR_BRANCH-squash"
  git merge --squash "origin/$CUR_BRANCH"
  git commit -a
  gpsetup
}

_parse-repo() {
  typeset -g MAIN_BRANCH DESTINATION ORIGIN_URL REPO

  MAIN_BRANCH="$(git_main_branch)"
  DESTINATION="${1:-$MAIN_BRANCH}"
  ORIGIN_URL="$(git remote get-url origin)"
  REPO="$(sed -rn 's/^.*:(.*)\.git/\1/p' <<<"$ORIGIN_URL")"
}

git:create-pr() {
  _parse-repo "$1"
  "$BROWSER" "https://github.com/$REPO/compare/$(urlencode "$DESTINATION")...$(urlencode "$(git_current_branch)")?expand=1"
}

git:create-mr() {
  _parse-repo "$1"
  "$BROWSER" "https://gitlab.com/$REPO/-/merge_requests/new?merge_request[source_branch]=$(urlencode "$(git_current_branch)")&merge_request[target_branch]=$(urlencode "$DESTINATION")"
}

git:create-mr-dev() {
  git:create-mr "$(git_develop_branch)"
}

git:create-pr-dev() {
  git:create-pr "$(git_develop_branch)"
}

git:download() {
  if [[ -z "$1" ]]; then
    echo "Please specify a git URL"
    return -1
  fi

  local CUR_DIR="$(pwd)"
  local GIT_URL="$1"
  local TARGET_DIR="${2:-$CUR_DIR}"
  local TRUNK

  TRUNK="$(echo "$GIT_URL" | sed 's/tree\/master/trunk/g')"

  echo "Downloading $TRUNK into $TARGET_DIR"

  cd "$TARGET_DIR" &&
    svn checkout $TRUNK

  cd "$CUR_DIR"
}

alias gcom='git:checkout-main'
alias gdtm='git:difftool-meld'
alias git_force_checks='git:force-checks'
alias glodev='git:log-origin-development'
alias glogd='git:log-divergence'
alias glom='git:log-origin-main'
alias gp='git:push'
alias gpr='git:prune'
alias gprune='git:pull-prune'
alias greview='git:review'
alias groh='git:reset-origin-hard'
alias gsquash='git:squash'
alias create-pr='git:create-pr'
alias create-mr='git:create-mr'
alias create-mr-dev='git:create-mr-dev'
alias create-pr-dev='git:create-pr-dev'
alias gdl='git:download'
