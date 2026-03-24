# Archie Migration Guide

This guide covers migration from Archie v2 to Archie v3.

Archie v2 used an `rsync`-based deployment flow. Archie v3 uses GNU Stow and
the `deployment-packages/` layout. Stow can be applied on top of a v2
deployment only after conflicting copied files are moved aside.

## v2 to v3

Choose the `p10k-*` package you want to keep, then back up conflicting files
based on the actual package contents:

```bash
SELECTED_P10K_PACKAGE="p10k-lean"
mkdir -p "$HOME/archie-pre-stow-backup"

backup_stow_conflicts() {
  local package_dir="$1"
  local deploy_root="$2"
  local backup_root="$3"

  fd '.' "$package_dir" --type f | while read -r file_to_deploy; do
    relative_path="${file_to_deploy#"$package_dir"/}"
    deployed_path="$deploy_root/$relative_path"
    backup_path="$backup_root/$relative_path"

    if [[ -e "$deployed_path" || -L "$deployed_path" ]]; then
      mkdir -p "$(dirname "$backup_path")"
      mv "$deployed_path" "$backup_path"
    fi
  done
}

backup_stow_conflicts_sudo() {
  local package_dir="$1"
  local deploy_root="$2"
  local backup_root="$3"

  sudo fd '.' "$package_dir" --type f | while read -r file_to_deploy; do
    relative_path="${file_to_deploy#"$package_dir"/}"
    deployed_path="$deploy_root/$relative_path"
    backup_path="$backup_root/$relative_path"

    if sudo test -e "$deployed_path" || sudo test -L "$deployed_path"; then
      sudo mkdir -p "$(dirname "$backup_path")"
      sudo mv "$deployed_path" "$backup_path"
    fi
  done
}

for package_name in home "$SELECTED_P10K_PACKAGE"; do
  backup_stow_conflicts \
    "deployment-packages/$package_name" \
    "$HOME" \
    "$HOME/archie-pre-stow-backup"
done

backup_stow_conflicts \
  "deployment-packages/config" \
  "$HOME/.config" \
  "$HOME/archie-pre-stow-backup/.config"

backup_stow_conflicts \
  "deployment-packages/local" \
  "$HOME/.local" \
  "$HOME/archie-pre-stow-backup/.local"

sudo mkdir -p /root/archie-pre-stow-backup

backup_stow_conflicts_sudo \
  "deployment-packages/etc" \
  "/etc" \
  "/root/archie-pre-stow-backup"

backup_stow_conflicts_sudo \
  "deployment-packages/xkb" \
  "/usr/share/xkeyboard-config-2" \
  "/root/archie-pre-stow-backup/usr-share-xkeyboard-config-2"
```

After that cleanup, deploy Archie v3:

```bash
stow --dir deployment-packages --target "$HOME" home
stow --dir deployment-packages --target "$HOME/.config" config
stow --dir deployment-packages --target "$HOME/.local" local
sudo stow --dir deployment-packages --target /etc etc
sudo stow --dir deployment-packages --target /usr/share/xkeyboard-config-2 xkb
stow --dir deployment-packages --target "$HOME" "$SELECTED_P10K_PACKAGE"
```

Preserve machine-specific local files that stay outside Stow management,
including:

- `~/.config/hypr/config/device.conf`
- `~/.config/hypr/hyprpaper.conf`
- `~/.local/lib/zsh/overrides.sh`

After the package deployment, continue with the setup steps in
[`docs/GUIDE.md`](./GUIDE.md), including the machine-specific `.dist`-derived
files and the optional theming steps.
