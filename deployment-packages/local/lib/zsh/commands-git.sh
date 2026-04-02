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

git:stash-commit() {
  local SPEC="${1:-HEAD}"
  local CURRENT_BRANCH CURRENT_HEAD TARGET_COMMIT PARENT_COMMIT COUNT STASH_LABEL

  CURRENT_BRANCH="$(git_current_branch)"

  if [[ -z "$CURRENT_BRANCH" ]]; then
    echo "You must start from a branch"
    return -1
  fi

  if [[ -n "$(git status --porcelain)" ]]; then
    echo "Working tree must be clean"
    return -1
  fi

  CURRENT_HEAD="$(git rev-parse --verify HEAD)"

  if [[ "$SPEC" =~ '^[0-9]+$' ]]; then
    COUNT="$SPEC"

    if [[ "$COUNT" -lt 1 ]]; then
      echo "Commit count must be at least 1"
      return -1
    fi

    if [[ "$COUNT" -eq 1 ]]; then
      TARGET_COMMIT="$CURRENT_HEAD"
    elif ! TARGET_COMMIT="$(git rev-parse --verify "HEAD~$((COUNT - 1))^{commit}" 2>/dev/null)"; then
      echo "Commit count exceeds branch history: $COUNT"
      return -1
    fi

    STASH_LABEL="last $COUNT commit(s)"
  else
    if ! TARGET_COMMIT="$(git rev-parse --verify "$SPEC^{commit}" 2>/dev/null)"; then
      echo "Invalid commit: $SPEC"
      return -1
    fi

    if ! git merge-base --is-ancestor "$TARGET_COMMIT" "$CURRENT_HEAD"; then
      echo "Commit must be HEAD or an ancestor of HEAD on $CURRENT_BRANCH"
      return -1
    fi

    STASH_LABEL="$SPEC..HEAD"
  fi

  if ! PARENT_COMMIT="$(git rev-parse --verify "${TARGET_COMMIT}~1" 2>/dev/null)"; then
    echo "Commit range must have a parent before its first commit: $SPEC"
    return -1
  fi

  gco "$PARENT_COMMIT" || return -1

  git checkout "$CURRENT_BRANCH" -- . || {
    gco "$CURRENT_BRANCH" >/dev/null 2>&1
    return -1
  }

  git stash push -m "stash from $STASH_LABEL" || {
    gco "$CURRENT_BRANCH" >/dev/null 2>&1
    return -1
  }

  gco "$CURRENT_BRANCH" || return -1
  git reset --hard "$PARENT_COMMIT"
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
alias gstashc='git:stash-commit'
alias gsquash='git:squash'
alias create-pr='git:create-pr'
alias create-mr='git:create-mr'
alias create-mr-dev='git:create-mr-dev'
alias create-pr-dev='git:create-pr-dev'
alias gdl='git:download'
