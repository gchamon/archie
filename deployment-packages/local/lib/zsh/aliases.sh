#!/usr/bin/env zsh
# Set personal aliases, overriding those provided by oh-my-zsh libs,
# plugins, and themes. Aliases can be placed here, though oh-my-zsh
# users are encouraged to define aliases within the ZSH_CUSTOM folder.
# For a full list of active aliases, run `alias`.
#
# Example aliases
# alias zshconfig="mate ~/.zshrc"
# alias ohmyzsh="mate ~/.oh-my-zsh"

[ "$TERM" = "xterm-kitty" ] && alias sshk="kitty +kitten ssh "

alias compton-restart="pkill compton && compton &> /dev/null &"
alias ffpm="firefox -ProfileManager "
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
alias ipyenv='pipenv run ipython'
alias jb_hcl_fix='sed -i --regexp-extended "s/registry.terraform.io\///g" **/.terraform/modules/modules.json && sed -i --regexp-extended "s/git::https:\/\/(.*)\.git/\1/" **/.terraform/modules/modules.json'
alias l='ls -l'
alias la='ls -a'
alias lla='ls -la'
alias ls='lsd '
alias lsh="l -sHi"
alias lt='ls --tree'
alias ltb='lt | bat'
alias myip='curl ipinfo.io/ip '
alias prettyjson='python -m json.tool'
# alias psgrep='ps -ax | grep '
alias scheme='rlwrap scheme'
alias sonar-branch='sonar-scanner -Dsonar.login=$SONAR_TOKEN -Dsonar.branch.name=$(git_current_branch) -Dsonar.branch.target=$(git_main_branch)'
alias sonar-main='sonar-scanner -Dsonar.login=$SONAR_TOKEN'
alias sudo="sudo "
alias vim="$VIM_BIN "

new_where() {
  ll $(which $1)
}
alias where='new_where '

# alias wl-paste='wl-paste -t text '

alias icat="kitten icat "

# pacmatic needs to be run as root: https://github.com/keenerd/pacmatic/issues/35
alias pacmatic='sudo --preserve-env=pacman_program /usr/bin/pacmatic'
alias docker-swarm-remote='docker -H ssh://${DOCKER_SWARM_REMOTE_HOST} '
alias docker-swarm-remote-deploy='docker-swarm stack deploy -c docker-compose.yml $(basename $PWD)'
alias docker-swarm-remote-rm='docker-swarm stack rm $(basename $PWD)'
alias docker-swarm-remote-redeploy='docker-swarm-rm && docker-swarm-deploy'
# alias terraform='tofu '
alias vm="vboxmanage "

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
function aider-build {
  docker build --pull -t aider-chat - <<EOF
FROM python:3.12
WORKDIR /app
RUN pip install aider-chat google-generativeai
ENTRYPOINT ["aider"]
EOF
}
alias aider-update="docker rmi aider-chat && docker system prune --force && aider-build"
