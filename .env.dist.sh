#!/bin/bash

# Archie script configuration
#
# Copy this file to ./.env.sh and edit that file to customize the repo-managed
# scripts. Scripts that source the shared bash library load ./.env.sh
# automatically when it exists.
#
# Example:
#   cp ./.env.dist.sh ./.env.sh
#   ${EDITOR:-vi} ./.env.sh
#   ./scripts/quickstart.sh
#
# Environment variables provided on the command line still take precedence:
#   ARCHIE_ENABLE_SDDM_THEME=0 ./scripts/quickstart.sh

# Quickstart

# When set to 1, quickstart installs the SDDM slice theme package and writes
# /etc/sddm.conf.d/theme.conf with Current=slice.
export ARCHIE_ENABLE_SDDM_THEME=1

# When set to 1, quickstart deploys Archie keyboard customizations into
# /usr/share/xkeyboard-config-2 via the xkb Stow package.
export ARCHIE_ENABLE_XKB_CUSTOMIZATIONS=0

# Destination path used when quickstart clones Archie outside an existing
# checkout.
export ARCHIE_CHECKOUT_DIR_NAME="$HOME/archie"

# Default Powerlevel10k Stow package that quickstart deploys for ~/.p10k.zsh.
export ARCHIE_P10K_PACKAGE="p10k-lean"

# GTK theme that quickstart writes to gtk-3.0/settings.ini,
# gtk-4.0/settings.ini, and best-effort gsettings.
export ARCHIE_GTK_THEME="Adwaita-dark"

# Backup roots used before Stow moves conflicting files aside.
export ARCHIE_USER_STOW_BACKUP_ROOT="$HOME/archie-pre-stow-backup"
export ARCHIE_SYSTEM_STOW_BACKUP_ROOT="/root/archie-pre-stow-backup"

# Reproducible base image scripts

# Bootstrap VM identity and published Incus image alias.
export ARCHIE_BASE_VM_NAME="archie-dev"
export ARCHIE_BASE_VM_HOSTNAME="archie-dev"
export ARCHIE_BASE_VM_USERNAME="archie"
export ARCHIE_BASE_SOURCE_IMAGE="images:archlinux/current/cloud"
export ARCHIE_BASE_IMAGE_ALIAS="archie/reproducible-baseline"

# Bootstrap VM sizing.
export ARCHIE_BASE_VM_CPU_LIMIT="4"
export ARCHIE_BASE_VM_MEMORY="8GiB"
export ARCHIE_BASE_VM_ROOT_DISK_SIZE="32GiB"

# Bootstrap VM SSH/bootstrap auth inputs.
export ARCHIE_BASE_SSH_PUBLIC_KEY_PATH="$HOME/.ssh/homelab.pub"
# export ARCHIE_BASE_VM_SSH_AUTHORIZED_KEY="ssh-ed25519 AAAA..."
# export ARCHIE_BASE_VM_PASSWORD_HASH='$6$...'

# Archie instance launch scripts

# Published image alias and launch-time guest settings.
export ARCHIE_INSTANCE_IMAGE_ALIAS="archie/reproducible-baseline"
export ARCHIE_INSTANCE_NAME="archie-dev-from-image"
export ARCHIE_INSTANCE_USERNAME="archie"
export ARCHIE_INSTANCE_REPO_URL="https://gitlab.com/gabriel.chamon/archie.git"
export ARCHIE_INSTANCE_SSH_IDENTITY="$HOME/.ssh/homelab"
export ARCHIE_INSTANCE_MEMORY="4GiB"

# Shared Incus wait tuning used by the dev-env scripts.
export ARCHIE_INCUS_AGENT_TIMEOUT_SECONDS="300"
export ARCHIE_INCUS_AGENT_POLL_SECONDS="2"

# Clipboard bridge helper

# Optional defaults for scripts/dev-env/ssh-clipboard-sync.sh. Command-line
# flags still win if you pass --identity or --interval explicitly.
export ARCHIE_CLIPBOARD_SYNC_IDENTITY=""
export ARCHIE_CLIPBOARD_SYNC_INTERVAL_SECONDS="1"

# Markdown TOC maintenance

# Markers used by maint-scripts/update-markdown-toc-build.sh.
export ARCHIE_TOC_START_MARKER="<!--toc:start-->"
export ARCHIE_TOC_END_MARKER="<!--toc:end-->"
export ARCHIE_TOC_IGNORE_MARKER="<!--toc:ignore-->"
export ARCHIE_TOC_HEADER_PLACEHOLDER="<!--toc:header-->"
