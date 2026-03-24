#!/usr/bin/env zsh

alias gcom='gco $(git_main_branch)'
alias gdtm='git difftool -t meld -y'
alias git_force_checks="gca! --no-edit && gp --force"
alias glodev="gl origin development"
alias glogd='git log origin/master..$(git_current_branch) --oneline --no-merges'
alias glom='gl origin $(git_main_branch)'
alias gp='ggpush'
alias gpr="git prune -v"
alias gprune="git pull --prune && git prune -v"
alias greview='if [[ "$(git_current_branch)" != review* ]]; then git checkout -b review/$(git_current_branch); fi && gpsetup'

gsquash() {
  if [[ "$1" == "" ]]; then
    echo "You must provide a target branch"
    return -1
  fi

  local CUR_BRANCH="$(git_current_branch)"
  local TARGET_BRANCH=$1
  git pull
  git commit -a -m "commiting rest of changes before squashing"
  gpsetup
  git checkout origin/$TARGET_BRANCH
  git checkout -b $CUR_BRANCH-squash
  git merge --squash origin/$CUR_BRANCH
  git commit -a
  gpsetup
}

_parse-repo() {
  MAIN_BRANCH=$(git_main_branch)
  DESTINATION="${1:-$MAIN_BRANCH}"
  ORIGIN_URL="$(git remote get-url origin)"
  REPO="$(sed -rn 's/^.*:(.*)\.git/\1/p' <<<$ORIGIN_URL)"
}

create-pr() {
  _parse-repo
  $BROWSER "https://github.com/$REPO/compare/$(urlencode $DESTINATION)...$(urlencode $(git_current_branch))?expand=1"
}

create-mr() {
  _parse-repo
  $BROWSER "https://gitlab.com/$REPO/-/merge_requests/new?merge_request[source_branch]=$(urlencode $(git_current_branch))&merge_request[target_branch]=${1:-$(git_main_branch)}"
}

alias create-mr-dev='create-mr $(git_develop_branch)'
alias create-pr-dev='create-pr $(git_develop_branch)'

gdl() {
  if [[ "$1" == "" ]]; then
    echo "Please specify a git URL"
    return -1
  fi

  local CUR_DIR="$(pwd)"
  local GIT_URL=$1
  local TARGET_DIR="${2:-$CUR_DIR}"
  local TRUNK="$(echo $GIT_URL | sed 's/tree\/master/trunk/g')"

  echo "Downloading $TRUNK into $TARGET_DIR"

  cd $TARGET_DIR &&
    svn checkout $TRUNK

  cd $CUR_DIR
}
