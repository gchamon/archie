#!/usr/bin/env zsh

alias ipyenv='pipenv run ipython'
alias jb_hcl_fix='sed -i --regexp-extended "s/registry.terraform.io\///g" **/.terraform/modules/modules.json && sed -i --regexp-extended "s/git::https:\/\/(.*)\.git/\1/" **/.terraform/modules/modules.json'
alias prettyjson='python -m json.tool'
alias aws:list-profiles='aws configure list-profiles'
alias sonar-branch='sonar-scanner -Dsonar.login=$SONAR_TOKEN -Dsonar.branch.name=$(git_current_branch) -Dsonar.branch.target=$(git_main_branch)'
alias sonar-main='sonar-scanner -Dsonar.login=$SONAR_TOKEN'
alias docker-swarm-remote='docker -H ssh://${DOCKER_SWARM_REMOTE_HOST} '
alias docker-swarm-remote-deploy='docker-swarm stack deploy -c docker-compose.yml $(basename $PWD)'
alias docker-swarm-remote-rm='docker-swarm stack rm $(basename $PWD)'
alias docker-swarm-remote-redeploy='docker-swarm-rm && docker-swarm-deploy'
alias vim:lazy-sync='nvim --headless -n -i NONE "+Lazy! sync" +qa'
alias vim:update='vim:lazy-sync'
alias vim:lazy-install='nvim --headless -n -i NONE "+Lazy! install" +qa'
alias vim:lazy-check='nvim --headless -n -i NONE "+Lazy! check" +qa'
alias vim:lazy-update='nvim --headless -n -i NONE "+Lazy! update" +qa'
alias vim:lazy-restore='nvim --headless -n -i NONE "+Lazy! restore" +qa'
alias vim:lazy-clean='nvim --headless -n -i NONE "+Lazy! clean" +qa'
alias vim:lazy-health='nvim --headless -n -i NONE "+Lazy health" +qa'
alias vim:health='nvim --headless -n -i NONE "+checkhealth" +qa'
alias vim:smoke='nvim --headless -n -i NONE "+qa"'

# Aider seems to be working from aider-venv package
# But it's outdated...
# alias aider="aider --no-auto-commits "
alias aider='docker run \
  -it --rm \
  --user $(id -u):$(id -g) \
  --env ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  --env GEMINI_API_KEY=$GEMINI_API_KEY \
  $(env | cut -f1 -d= | sed "s/^/-e /") \
  -v $(git rev-parse --show-toplevel):/app \
  -v $HOME/.config/aider:$HOME/.config/aider:ro \
  -v $HOME/.aider:$HOME/.aider \
  -v $HOME/.gitconfig:$HOME/.gitconfig \
  aider-chat --config $HOME/.config/aider/config.yaml --no-auto-commits '
alias aider-update="docker rmi aider-chat && docker system prune --force && aider-build"

aider-build() {
  docker build --pull -t aider-chat - <<EOF
FROM python:3.12
WORKDIR /app
RUN pip install aider-chat google-generativeai
ENTRYPOINT ["aider"]
EOF
}

terraform-remote-plan() {
  terraform-enable-remote &&
    terraform plan $1 &&
    terraform-disable-remote
}

terraform-enable-remote() {
  sed -i -r "s/(\/\/ )*(.*)/\2/" $(rg -l 'backend "remote"')
  terraform init
}

terraform-disable-remote() {
  sed -i -r "s/^(\/\/ )*(.*)/\/\/ \2/" $(rg -l 'backend "remote"')
  terraform init -migrate-state
}

terraform-update-state() {
  rm terraform.tfstate*
  terraform-enable-remote
  terraform-disable-remote
}

terraform-bulk() {
  cmd=${2:-echo}
  rg=${1}
  for res in $(terraform state list); do
    if [[ "$res" =~ "$rg" ]]; then
      eval "$cmd '$res'"
    fi
  done
}

cclip() {
  cat $1 | xclip -selection clipboard
}

ccopy() {
  cat $1 | wl-copy
}

_cliphist:squash() {
  local order="$1"
  shift

  local count="${1:-}"
  if [[ ! "$count" =~ '^[1-9][0-9]*$' ]]; then
    echo "Usage: cliphist:squash-${order} <positive-count>" >&2
    return 1
  fi

  local output_file
  local entry_file
  local list_file
  output_file="$(mktemp)"
  entry_file="$(mktemp)"
  list_file="$(mktemp)"

  {
    local copied_entries=0
    local input
    cliphist list | head -n "$count" >"$list_file"
    if [[ "$order" == fifo ]]; then
      tac "$list_file" >"${list_file}.ordered"
      mv "${list_file}.ordered" "$list_file"
    fi

    while read -r input; do
      cliphist decode "$input" >"$entry_file"

      local mime_type="$(file --mime-type -b "$entry_file")"
      if [[ "$mime_type" == text/* || "$mime_type" == "application/json" || "$mime_type" == "application/xml" ]]; then
        cat "$entry_file" >>"$output_file"
        echo >>"$output_file"
        ((copied_entries++))
      fi
    done <"$list_file"

    if ((copied_entries == 0)); then
      echo "cliphist:squash-${order}: no text clipboard entries found" >&2
      return 1
    fi

    wl-copy <"$output_file"
  } always {
    rm -f "$output_file" "$entry_file" "$list_file" "${list_file}.ordered"
  }
}

cliphist:squash-fifo() {
  _cliphist:squash fifo "$@"
}

cliphist:squash-lifo() {
  _cliphist:squash lifo "$@"
}

alias cliphist:squash=cliphist:squash-fifo

urlencode() {
  jq -rn --arg x $1 '$x|@uri'
}

urldecode() {
  local data=${1//+/ }
  printf '%b' "${data//%/\x}"
}

beautify-clipboard() {
  wl-paste | jq -r . | wl-copy
}

minify-clipboard() {
  wl-paste | jq -cr . | wl-copy
}

exec-script() {
  bash $HOME/Scripts/
}

lxc-purge-vms() {
  server="${1:-local}"
  lxc ls $server: --format json |
    jq -rc '.[].name' |
    xargs -I '{}' lxc rm --force $server:{}
}

decode_jwt() {
  if [[ -f $1 ]]; then
    JWT_CONTENTS=$(cat $1)
  else
    JWT_CONTENTS=$1
  fi
  local header=$(urldecode $(echo $JWT_CONTENTS | cut -d . -f 1 | base64 -d))
  local payload=$(urldecode $(echo $JWT_CONTENTS | cut -d . -f 2 | base64 -d))
  jq -n --argjson header "$header" --argjson payload "$payload" '[$header, $payload]'
}

elixir-new-module() {
  local module_name="$1"
  local root_dir="."
  if [ -z "$module_name" ]; then
    echo "Usage: create_elixir_module <ModuleName>"
    echo "Example: create_elixir_module MyApp.Mailer"
    return 1
  fi

  local module_path=$(
    echo "$module_name" |
      sed 's/\./\//g' |
      perl -pe 's/(?<=[a-z])([A-Z])/_\1/g; s/(?<=[A-Z])([A-Z][a-z])/_\1/g' |
      tr '[:upper:]' '[:lower:]'
  )

  local module_file="${root_dir}/lib/${module_path}.ex"
  local test_file="${root_dir}/test/${module_path}_test.exs"
  local module_dir=$(dirname "$module_file")
  local test_dir=$(dirname "$test_file")

  if ! mkdir -p "$module_dir"; then
    echo "Error: Failed to create directory $module_dir"
    return 1
  fi

  if ! mkdir -p "$test_dir"; then
    echo "Error: Failed to create directory $test_dir"
    return 1
  fi

  if [ -f "$module_file" ]; then
    echo "Error: Module file already exists: $module_file"
    return 1
  fi

  cat <<EOF >"$module_file"
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

  if [ -f "$test_file" ]; then
    echo "Error: Test file already exists: $test_file"
    return 1
  fi

  cat <<EOF >"$test_file"
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

  local container_id="$(
    tr -dc A-Za-z0-9 </dev/urandom | head -c 8
    echo
  )"
  docker run -it --rm \
    -v "$PWD:/app" \
    --workdir /app \
    --name docker-run-in-cwd-$container_id \
    $extra_args \
    $image "$cmd"
}

_vim:require-args() {
  local command_name="$1"
  local usage="$2"
  shift 2

  if (( $# == 0 )); then
    echo "Usage: ${command_name} ${usage}" >&2
    return 1
  fi
}

_vim:require-file() {
  local command_name="$1"
  local file_path="${2:-}"

  if [[ -z "$file_path" ]]; then
    echo "Usage: ${command_name} <path>" >&2
    return 1
  fi

  if [[ ! -f "$file_path" ]]; then
    echo "${command_name}: file not found: $file_path" >&2
    return 1
  fi
}

_vim:require-filetype() {
  local command_name="$1"
  local filetype="${2:-}"

  if [[ -z "$filetype" ]]; then
    echo "Usage: ${command_name} <filetype> [path...]" >&2
    return 1
  fi

  if [[ ! "$filetype" =~ '^[A-Za-z0-9_.+-]+$' ]]; then
    echo "${command_name}: invalid filetype: $filetype" >&2
    return 1
  fi
}

_vim:lua-string-list() {
  local lua_args=""
  local arg
  local escaped

  for arg in "$@"; do
    escaped="${arg//\\/\\\\}"
    escaped="${escaped//\"/\\\"}"
    lua_args="${lua_args}\"${escaped}\","
  done

  printf "{%s}" "$lua_args"
}

_vim:nvim() {
  local runtime_dir="${NVIM_ADMIN_RUNTIME_DIR:-${TMPDIR:-/tmp}/nvim-admin-${UID}}"
  mkdir -p "$runtime_dir/state" "$runtime_dir/cache"
  XDG_STATE_HOME="$runtime_dir/state" XDG_CACHE_HOME="$runtime_dir/cache" nvim --headless -n -i NONE "$@"
}

vim:filetype() {
  local filetype="${1:-}"
  _vim:require-filetype vim:filetype "$filetype" || return 1
  shift

  if (( $# == 0 )) && [[ ! -t 0 ]]; then
    nvim -c "setlocal filetype=${filetype}" -
    return
  fi

  nvim -c "setlocal filetype=${filetype}" -- "$@"
}

alias vim:ft=vim:filetype

_vim:admin() {
  local command_name="$1"
  local helper_path="${ZSHLIB:-$HOME/.local/lib/zsh}/nvim-admin.lua"
  shift

  NVIM_ADMIN_LUA="$helper_path" _vim:nvim "$@" -c "lua dofile(vim.env.NVIM_ADMIN_LUA).run('${command_name}')" -c qall
}

vim:mason-update() {
  _vim:nvim -c "MasonUpdate" -c qall
}

vim:mason-install() {
  _vim:require-args vim:mason-install "<package...>" "$@" || return 1
  _vim:nvim -c "MasonInstall $*" -c qall
}

vim:mason-uninstall() {
  _vim:require-args vim:mason-uninstall "<package...>" "$@" || return 1
  _vim:nvim -c "MasonUninstall $*" -c qall
}

vim:lsp-install() {
  _vim:require-args vim:lsp-install "<server...>" "$@" || return 1
  _vim:nvim -c "LspInstall $*" -c qall
}

vim:lsp-uninstall() {
  _vim:require-args vim:lsp-uninstall "<server...>" "$@" || return 1
  _vim:nvim -c "LspUninstall $*" -c qall
}

vim:ts-update() {
  local parsers
  parsers="$(_vim:lua-string-list "$@")"
  _vim:nvim -c "lua require('nvim-treesitter').update(${parsers}, { summary = true }):await()" -c qall
}

vim:ts-install() {
  _vim:require-args vim:ts-install "<parser...>" "$@" || return 1
  local parsers
  parsers="$(_vim:lua-string-list "$@")"
  _vim:nvim -c "lua require('nvim-treesitter').install(${parsers}, { summary = true }):await()" -c qall
}

vim:ts-uninstall() {
  _vim:require-args vim:ts-uninstall "<parser...>" "$@" || return 1
  local parsers
  parsers="$(_vim:lua-string-list "$@")"
  _vim:nvim -c "lua require('nvim-treesitter').uninstall(${parsers}, { summary = true }):await()" -c qall
}

vim:lazy-list() {
  _vim:admin lazy_list
}

vim:mason-list() {
  _vim:admin mason_list
}

vim:lsp-list() {
  _vim:admin lsp_list
}

vim:ts-list() {
  _vim:admin ts_list
}

vim:file-lsps() {
  _vim:require-file vim:file-lsps "$1" || return 1
  NVIM_DEBUG_FILE="$1" _vim:admin file_lsps
}

vim:file-parsers() {
  _vim:require-file vim:file-parsers "$1" || return 1
  NVIM_DEBUG_FILE="$1" _vim:admin file_parsers
}

vim:file-plugins() {
  _vim:require-file vim:file-plugins "$1" || return 1
  NVIM_DEBUG_FILE="$1" _vim:admin file_plugins
}

vim:file-debug() {
  _vim:require-file vim:file-debug "$1" || return 1
  NVIM_DEBUG_FILE="$1" _vim:admin file_debug
}
