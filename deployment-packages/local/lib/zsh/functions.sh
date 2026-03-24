#!/usr/bin/env zsh

function terraform-remote-plan {
  terraform-enable-remote &&
    terraform plan $1 &&
    terraform-disable-remote
}

function terraform-enable-remote {
  sed -i -r "s/(\/\/ )*(.*)/\2/" $(rg -l 'backend "remote"')
  terraform init
}

function terraform-disable-remote {
  sed -i -r "s/^(\/\/ )*(.*)/\/\/ \2/" $(rg -l 'backend "remote"')
  terraform init -migrate-state
}

function terraform-update-state {
  rm terraform.tfstate*
  terraform-enable-remote
  terraform-disable-remote
}

rgx () {
  echo $1 | rg -e $2;
}

autoremove() {
	PKGS=$(yay -Qdtq);
	yay -Rcns $PKGS;
}

cclip() {
  cat $1 | xclip -selection clipboard;
}

ccopy() {
  cat $1 | wl-copy
}

# git push with squash
gsquash() {
  if [[ "$1" == "" ]];
  then
    echo "You must provide a target branch";
    return -1;
  fi

  local CUR_BRANCH="$(git_current_branch)";
  local TARGET_BRANCH=$1;
  git pull;
  git commit -a -m "commiting rest of changes before squashing";
  gpsetup;
  git checkout origin/$TARGET_BRANCH;
  git checkout -b $CUR_BRANCH-squash;
  git merge --squash origin/$CUR_BRANCH;
  git commit -a;
  gpsetup;
}

_parse-repo () {
  MAIN_BRANCH=$(git_main_branch)
  DESTINATION="${1:-$MAIN_BRANCH}"
  ORIGIN_URL="$(git remote get-url origin)"
  REPO="$(sed -rn 's/^.*:(.*)\.git/\1/p' <<< $ORIGIN_URL)"
}

# for github
create-pr() {
  _parse-repo
  $BROWSER "https://github.com/$REPO/compare/$(urlencode $DESTINATION)...$(urlencode $(git_current_branch))?expand=1"
}

# for gitlab
create-mr() {
  _parse-repo
  $BROWSER "https://gitlab.com/$REPO/-/merge_requests/new?merge_request[source_branch]=$(urlencode $(git_current_branch))&merge_request[target_branch]=${1:-main}"
}

gdl () {
  if [[ "$1" == "" ]];
  then
    echo "Please specify a git URL";
    return -1;
  fi

  local CUR_DIR="$(pwd)"
  local GIT_URL=$1
  local TARGET_DIR="${2:-$CUR_DIR}"
  local TRUNK="$(echo $GIT_URL | sed 's/tree\/master/trunk/g')"

  echo "Downloading $TRUNK into $TARGET_DIR";

  cd $TARGET_DIR &&
  svn checkout $TRUNK;

  cd $CUR_DIR;
}

function terraform-bulk {
  cmd=${2:-echo}
  rg=${1}
  for res in $(terraform state list); do
    if [[ "$res" =~ "$rg" ]]; then
      eval "$cmd '$res'"
    fi
  done
}

function urlencode {
  jq -rn --arg x $1 '$x|@uri'
}

function urldecode {
    local data=${1//+/ }
    printf '%b' "${data//%/\x}"
}

function beautify-clipboard {
  wl-paste | jq -r . | wl-copy
}

function minify-clipboard {
  wl-paste | jq -cr . | wl-copy
}

# function to clear the terminal scrollback, effectively purging the terminal session of all interaction data
clear_scrollback() {
    printf '\033[2J\033[3J\033[1;1H'
}

exec-script() {
  bash $HOME/Scripts/
}

cpi() {
  rsync -va --progress "$@"
}

lxc-purge-vms() {
  server="${1:-local}"
  lxc ls $server: --format json \
    | jq -rc '.[].name' \
    | xargs -I '{}' lxc rm --force $server:{}
}

decode_jwt(){
  if [[ -f $1 ]]; then
    JWT_CONTENTS=$(cat $1)
  else;
    JWT_CONTENTS=$1
  fi
  local header=$(urldecode $(echo $JWT_CONTENTS | cut -d . -f 1 | base64 -d))
  local payload=$(urldecode $(echo $JWT_CONTENTS | cut -d . -f 2 | base64 -d))
  jq -n --argjson header "$header" --argjson payload "$payload" '[$header, $payload]'
}

elixir-new-module () {
    local module_name="$1" 
    local root_dir="." 
    if [ -z "$module_name" ]
    then
        echo "Usage: create_elixir_module <ModuleName>"
        echo "Example: create_elixir_module MyApp.Mailer"
        return 1
    fi
    
    # Convert CamelCase to underscore_case for each module part
    local module_path=$(
        echo "$module_name" \
        | sed 's/\./\//g' \
        | perl -pe 's/(?<=[a-z])([A-Z])/_\1/g; s/(?<=[A-Z])([A-Z][a-z])/_\1/g' \
        | tr '[:upper:]' '[:lower:]'
    )
    
    local module_file="${root_dir}/lib/${module_path}.ex" 
    local test_file="${root_dir}/test/${module_path}_test.exs" 
    local module_dir=$(dirname "$module_file") 
    local test_dir=$(dirname "$test_file") 
    
    if ! mkdir -p "$module_dir"
    then
        echo "Error: Failed to create directory $module_dir"
        return 1
    fi
    
    if ! mkdir -p "$test_dir"
    then
        echo "Error: Failed to create directory $test_dir"
        return 1
    fi
    
    if [ -f "$module_file" ]
    then
        echo "Error: Module file already exists: $module_file"
        return 1
    fi
    
    cat <<EOF > "$module_file"
defmodule $module_name do
  @moduledoc """
  Documentation for \`$module_name\`.
  """

  # Example function - replace with your logic
  def hello do
    :world
  end
end
EOF
    
    if [ -f "$test_file" ]
    then
        echo "Error: Test file already exists: $test_file"
        return 1
    fi
    
    cat <<EOF > "$test_file"
defmodule ${module_name}Test do
  use ExUnit.Case
  doctest $module_name

  describe "$module_name basic functionality" do
    test "the truth" do
      assert 1 + 1 == 2
    end

    # Example test for the boilerplate hello/0 function
    test "hello/0 returns :world" do
      assert $module_name.hello() == :world
    end
  end
end
EOF
    
    echo "Successfully created the following files:"
    lsd -1 "$module_file" "$test_file"
}

docker-run-in-cwd() {
  local image="${1:-ubuntu:24.04}"
  local cmd="${2:-bash}"
  local extra_args="${3:-}"

  local container_id="$(tr -dc A-Za-z0-9 </dev/urandom | head -c 8; echo)"
  docker run -it --rm \
    -v "$PWD:/app" \
    --workdir /app \
    --name docker-run-in-cwd-$container_id \
    $extra_args \
    $image "$cmd"
}

de-reload() {
  hyprctl reload
  sleep 5
  hyprctl reload
}

psgrep() {
  ps -ax | grep $1 | grep -v grep
}

dunst-history() {
  dunstctl history |
    jq -cr '.data | flatten(1) | .[] | {"html_text": .message.data, "timestamp": .timestamp.data}' |
    while read -r notification_data; do
      html_text=$(jq -r '.html_text' <<<$notification_data)
      timestamp=$(jq -r '.timestamp' <<<$notification_data)
      rendered=$(html2text <<<$html_text)
      if [[ -n $rendered ]]; then
        # Get the system boot time in seconds + your timestamp converted to seconds
        converted_timestamp=$(bc <<<"$(stat -c %Y /proc/1) + ($timestamp / 1000000)")
        rendered_timestamp=$(date +"%Y-%m-%dT%H:%M:%S%z" -d "@$converted_timestamp")
        echo timestamp: $rendered_timestamp
        echo message: $rendered
        echo ---------------------------------------
      fi
    done
}
