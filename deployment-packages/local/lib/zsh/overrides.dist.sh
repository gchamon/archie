#!/usr/bin/env zsh

# Template for machine-specific zsh overrides.
#
# Runtime path:
#   ~/.local/lib/zsh/overrides.sh
#
# This file is tracked as a template only. Create a local `overrides.sh` beside
# the deployed template target and keep it untracked. In a Stow deployment, the
# deployed `.dist` file is a symlink, so resolve its real location with
# `readlink` before creating your local override file next to it.
#
# Example:
#   template_path="$(readlink "$HOME/.local/lib/zsh/overrides.dist.sh")"
#   override_dir="$(dirname "$template_path")"
#   ${EDITOR:-nvim} "$override_dir/overrides.sh"
#
# The overrides below are intentionally additive. Use this file to extend the
# base values defined in `~/.zshrc` without editing the tracked Stow-managed
# files directly.

# Extend the default Oh My Zsh plugin list from `~/.zshrc`.
# Base value:
#   plugins=(git extract fzf docker docker-compose terraform)
#
# Uncomment to enable extra plugins on this machine only.
# plugins+=(kubectl kube-ps1)
