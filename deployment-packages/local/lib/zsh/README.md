# Zsh Library

<!--toc:start-->

- [Zsh Library](#zsh-library)
  - [`commands.sh`](#commandssh)
  - [`commands-core.sh`](#commands-coresh)
  - [`commands-git.sh`](#commands-gitsh)
  - [`commands-system.sh`](#commands-systemsh)
  - [`commands-devtools.sh`](#commands-devtoolssh)
  - [`commands-pacman.sh`](#commands-pacmansh)
  - [`overrides.dist.sh`](#overridesdistsh)
<!--toc:end-->

This folder contains shell commands loaded by `~/.zshrc`. The main entrypoint is `commands.sh`, which sources the command modules below.

## `commands.sh`

| Name | Kind | Description |
| --- | --- | --- |
| `commands.sh` | Loader | Sources the command modules in a fixed order: core, git, system, devtools, pacman. |

## `commands-core.sh`

| Name | Kind | Description |
| --- | --- | --- |
| `sshk` | Alias | Runs Kitty's SSH kitten when the terminal is `xterm-kitty`. |
| `sudo` | Alias | Preserves alias expansion after `sudo`. |
| `vim` | Alias | Runs the editor from `$VIM_BIN`, or `/usr/bin/vim` when `VIM_BIN` is unset. |
| `where` | Alias | Shortcut to `new_where`. |
| `icat` | Alias | Runs Kitty image display. |
| `l` | Alias | `ls -l`. |
| `la` | Alias | `ls -a`. |
| `lla` | Alias | `ls -la`. |
| `ls` | Alias | Uses `lsd` instead of plain `ls`. |
| `lsh` | Alias | Human-readable size listing. |
| `lt` | Alias | Tree view listing. |
| `ltb` | Alias | Tree view piped through `bat`. |
| `new_where` | Function | Shows a long listing for the resolved command path. |
| `rgx` | Function | Pipes a string into `rg` with the provided pattern. |
| `clear_scrollback` | Function | Clears the terminal and scrollback buffer. |
| `psgrep` | Function | Searches running processes and filters out the `grep` process itself. |

## `commands-git.sh`

| Name | Kind | Description |
| --- | --- | --- |
| `git:checkout-main` | Function | Checks out the repo main branch. |
| `git:difftool-meld` | Function | Opens Git diffs in Meld. |
| `git:force-checks` | Function | Creates a fixup commit and force-pushes. |
| `git:log-origin-development` | Function | Pulls log/history from `origin/development`. |
| `git:log-divergence` | Function | Shows commits between `origin/master` and the current branch. |
| `git:log-origin-main` | Function | Pulls log/history from `origin/<main>`. |
| `git:push` | Function | Uses `ggpush` as the default push command. |
| `git:prune` | Function | Runs `git prune -v`. |
| `git:pull-prune` | Function | Pulls with prune, then prunes local refs. |
| `git:review` | Function | Creates a `review/*` branch if needed and runs `gpsetup`. |
| `git:stash-commit` | Function | Turns `HEAD` or a contiguous commit range ending at `HEAD` into a stash entry, returns to the original branch, and rewinds the branch to just before that range. |
| `git:squash` | Function | Builds a squash branch on top of a target branch. |
| `git:create-pr` | Function | Opens a GitHub compare page for the current branch. |
| `git:create-mr` | Function | Opens a GitLab merge request page for the current branch. |
| `git:create-mr-dev` | Function | Opens a GitLab merge request page targeting the develop branch. |
| `git:create-pr-dev` | Function | Opens a GitHub compare page targeting the develop branch. |
| `git:download` | Function | Downloads a sub-tree URL via Subversion checkout. |
| `gcom` | Alias | Checks out the repo main branch. |
| `gdtm` | Alias | Opens Git diffs in Meld. |
| `git_force_checks` | Alias | Creates a fixup commit and force-pushes. |
| `glodev` | Alias | Pulls log/history from `origin/development`. |
| `glogd` | Alias | Shows commits between `origin/master` and the current branch. |
| `glom` | Alias | Pulls log/history from `origin/<main>`. |
| `gp` | Alias | Uses `ggpush` as the default push command. |
| `gpr` | Alias | Runs `git prune -v`. |
| `gprune` | Alias | Pulls with prune, then prunes local refs. |
| `greview` | Alias | Creates a `review/*` branch if needed and runs `gpsetup`. |
| `gstashc` | Alias | Shorthand alias for `git:stash-commit` ("git stash commit"). |
| `gsquash` | Alias | Compatibility alias for `git:squash`. |
| `_parse-repo` | Function | Internal helper that derives repo and destination branch metadata. |
| `create-pr` | Alias | Compatibility alias for `git:create-pr`. |
| `create-mr` | Alias | Compatibility alias for `git:create-mr`. |
| `create-mr-dev` | Alias | Compatibility alias for `git:create-mr-dev`. |
| `create-pr-dev` | Alias | Compatibility alias for `git:create-pr-dev`. |
| `gdl` | Alias | Compatibility alias for `git:download`. |

## `commands-system.sh`

| Name | Kind | Description |
| --- | --- | --- |
| `compton-restart` | Alias | Restarts Compton in the background. |
| `ffpm` | Alias | Opens Firefox profile manager. |
| `myip` | Alias | Prints the public IP address. |
| `scheme` | Alias | Starts `scheme` under `rlwrap`. |
| `vm` | Alias | Runs `vboxmanage`. |
| `cpi` | Function | Copies files with `rsync --progress`. |
| `de-reload` | Function | Reloads Hyprland twice with a short delay. |
| `dunst-history` | Function | Prints Dunst notification history in a readable text format. |

## `commands-devtools.sh`

| Name | Kind | Description |
| --- | --- | --- |
| `ipyenv` | Alias | Starts IPython inside Pipenv. |
| `jb_hcl_fix` | Alias | Rewrites Terraform module metadata paths in `.terraform` state. |
| `prettyjson` | Alias | Pretty-prints JSON with Python. |
| `sonar-branch` | Alias | Runs `sonar-scanner` for the current branch. |
| `sonar-main` | Alias | Runs `sonar-scanner` for the main branch/default config. |
| `docker-swarm-remote` | Alias | Runs Docker against a remote swarm host over SSH. |
| `docker-swarm-remote-deploy` | Alias | Deploys the current directory as a swarm stack. |
| `docker-swarm-remote-rm` | Alias | Removes the current directory swarm stack. |
| `docker-swarm-remote-redeploy` | Alias | Removes then redeploys the current directory swarm stack. |
| `aider` | Alias | Runs `aider` inside a prepared Docker container. |
| `aider-update` | Alias | Rebuilds the local `aider` image after cleanup. |
| `aider-build` | Function | Builds the local `aider-chat` image. |
| `terraform-remote-plan` | Function | Enables remote Terraform state, runs `plan`, then disables it again. |
| `terraform-enable-remote` | Function | Uncomments remote backend config and runs `terraform init`. |
| `terraform-disable-remote` | Function | Comments remote backend config and migrates state back. |
| `terraform-update-state` | Function | Removes local state files and cycles remote state on/off. |
| `terraform-bulk` | Function | Runs a command for each Terraform state entry matching a regex. |
| `cclip` | Function | Copies a file into the X11 clipboard. |
| `ccopy` | Function | Copies a file into the Wayland clipboard. |
| `urlencode` | Function | URL-encodes a string with `jq`. |
| `urldecode` | Function | URL-decodes a string. |
| `beautify-clipboard` | Function | Pretty-prints JSON from the clipboard back into the clipboard. |
| `minify-clipboard` | Function | Minifies JSON from the clipboard back into the clipboard. |
| `aws:list-profiles` | Function | Prints AWS CLI profile names from `~/.aws/config` or `$AWS_CONFIG_FILE`. |
| `exec-script` | Function | Runs a script from `$HOME/Scripts/`. |
| `lxc-purge-vms` | Function | Deletes all Incus/LXC instances on a server. |
| `decode_jwt` | Function | Decodes a JWT from a file or string and prints header/payload JSON. |
| `elixir-new-module` | Function | Scaffolds an Elixir module and matching test file. |
| `docker-run-in-cwd` | Function | Starts a disposable container with the current directory mounted at `/app`. |

## `commands-pacman.sh`

| Name | Kind | Description |
| --- | --- | --- |
| `pacmatic` | Alias | Runs `pacmatic` under `sudo` while preserving `pacman_program`. |
| `_pkg:require-arg` | Function | Internal helper that validates a required package/search argument. |
| `autoremove` | Function | Removes orphaned packages with `yay -Rcns`. |
| `pacman:installed` | Function | Lists installed packages. |
| `pacman:manual` | Function | Lists manually installed packages. |
| `pacman:deps` | Function | Lists packages installed as dependencies. |
| `pacman:orphans` | Function | Lists orphaned packages. |
| `pacman:foreign` | Function | Lists foreign packages not in the official repos. |
| `pacman:search` | Function | Searches package repositories with `pacman -Ss`. |
| `pacman:info` | Function | Shows installed or repo package metadata for a package. |
| `pacman:files` | Function | Lists files shipped by a package. |
| `pacman:owns` | Function | Shows which package owns a file. |
| `pacman:install` | Function | Installs packages with `pacman -S`. |
| `pacman:remove` | Function | Removes packages with `pacman -R`. |
| `pacman:remove-deps` | Function | Removes packages and now-unused dependencies with `pacman -Rns`. |
| `pacman:update` | Function | Runs a full system update with `pacman -Syu`. |
| `pacman:refresh` | Function | Refreshes package databases with `pacman -Sy`. |
| `pacman:clean` | Function | Cleans old package cache entries. |
| `pacman:clean-all` | Function | Aggressively clears the package cache. |
| `yay:installed` | Function | Lists installed packages through `yay`. |
| `yay:search` | Function | Searches repos and AUR with `yay -Ss`. |
| `yay:info` | Function | Shows package metadata through `yay`. |
| `yay:install` | Function | Installs packages with `yay -S`. |
| `yay:remove` | Function | Removes packages with `yay -R`. |
| `yay:update` | Function | Runs a full system and AUR update with `yay -Syu`. |
| `yay:clean` | Function | Cleans package cache through `yay`. |
| `yay:orphans` | Function | Prints orphaned packages or a friendly "none found" message. |
| `yay:purge-orphans` | Function | Removes orphaned packages with `yay -Rcns`. |

## `overrides.dist.sh`

| Name | Kind | Description |
| --- | --- | --- |
| `overrides.dist.sh` | Template | Placeholder for a machine-specific `overrides.sh` file created locally next to the deployed template target. |
| `plugins+=(kubectl kube-ps1)` | Example override | Appends extra Oh My Zsh plugins on a single machine without changing the tracked base plugin list in `~/.zshrc`. |
