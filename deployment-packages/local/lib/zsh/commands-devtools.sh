#!/usr/bin/env zsh

alias ipyenv='pipenv run ipython'
alias jb_hcl_fix='sed -i --regexp-extended "s/registry.terraform.io\///g" **/.terraform/modules/modules.json && sed -i --regexp-extended "s/git::https:\/\/(.*)\.git/\1/" **/.terraform/modules/modules.json'
alias prettyjson='python -m json.tool'
alias sonar-branch='sonar-scanner -Dsonar.login=$SONAR_TOKEN -Dsonar.branch.name=$(git_current_branch) -Dsonar.branch.target=$(git_main_branch)'
alias sonar-main='sonar-scanner -Dsonar.login=$SONAR_TOKEN'
alias docker-swarm-remote='docker -H ssh://${DOCKER_SWARM_REMOTE_HOST} '
alias docker-swarm-remote-deploy='docker-swarm stack deploy -c docker-compose.yml $(basename $PWD)'
alias docker-swarm-remote-rm='docker-swarm stack rm $(basename $PWD)'
alias docker-swarm-remote-redeploy='docker-swarm-rm && docker-swarm-deploy'

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

urlencode() {
  jq -rn --arg x $1 '$x|@uri'
}

urldecode() {
  local data=${1//+/ }
  printf '%b' "${data//%/\x}"
}

aws:list-profiles() {
  local config_file="${AWS_CONFIG_FILE:-$HOME/.aws/config}"

  if [[ ! -f "$config_file" ]]; then
    echo "AWS config not found: $config_file" >&2
    return 1
  fi

  yq -p=ini -oy 'to_entries | .[] | select(.key | test("^profile ")) | .key' "$config_file" |
    cut -d' ' -f2
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
