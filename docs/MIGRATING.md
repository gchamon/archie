# Archie Migration Guide

This guide covers migration from Archie v2 to Archie v3.

Archie v2 used an `rsync`-based deployment flow. Archie v3 uses GNU Stow and
the `deployment-packages/` layout. Stow can be applied on top of a v2
deployment only after conflicting copied files are moved aside.

## v2 to v3

In v3, the deployment method changed from `rsync` copies to `stow` managed
symlinks.

### Migrating

Choose the `p10k-*` package you want to keep, then back up conflicting files
based on the actual package contents. This covers `home`, the selected
Powerlevel10k package, `config`, `local`, and the system-level `etc` and
`xkb` packages when the old deployment also copied files into `/etc` or
`/usr/share/xkeyboard-config-2`:

```bash
SELECTED_P10K_PACKAGE="p10k-lean"
mkdir -p "$HOME/archie-pre-stow-backup"

backup_stow_conflicts() {
  local package_dir="$1"
  local deploy_root="$2"
  local backup_root="$3"

  fd '.' "$package_dir" --type f --hidden | while read -r file_to_deploy; do
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

  sudo fd '.' "$package_dir" --type f --hidden | while read -r file_to_deploy; do
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

After the conflicting copied files have been moved aside, deploy Archie v3:

```bash
stow --dir deployment-packages --target "$HOME" home
stow --dir deployment-packages --target "$HOME" "$SELECTED_P10K_PACKAGE"
stow --dir deployment-packages --target "$HOME/.config" config
stow --dir deployment-packages --target "$HOME/.local" local
sudo stow --dir deployment-packages --target /etc etc
sudo stow --dir deployment-packages --target /usr/share/xkeyboard-config-2 xkb
```

Preserve machine-specific local files that stay outside Stow management,
including:

- `~/.config/hypr/config/device.conf`
- `~/.config/hypr/hyprpaper.conf`
- `~/.local/lib/zsh/overrides.sh`

After the package deployment, continue with the setup steps in
[`docs/GUIDE.md`](./GUIDE.md), including the machine-specific `.dist`-derived
files and the optional theming steps.

### Restore after a failed migration

If the migration is not successful and you need to return to the pre-Stow
state, first remove the Stow-managed links that were just created:

```bash
stow --dir deployment-packages --target "$HOME" --delete home
stow --dir deployment-packages --target "$HOME" --delete "$SELECTED_P10K_PACKAGE"
stow --dir deployment-packages --target "$HOME/.config" --delete config
stow --dir deployment-packages --target "$HOME/.local" --delete local
sudo stow --dir deployment-packages --target /etc --delete etc
sudo stow --dir deployment-packages --target /usr/share/xkeyboard-config-2 --delete xkb
```

Restore the backed-up home, XDG, local library and system files:

```bash
fd '.' "$HOME/archie-pre-stow-backup" --type f --hidden | while read -r backup_file; do
  relative_path="${backup_file#"$HOME/archie-pre-stow-backup"/}"
  restore_path="$HOME/$relative_path"

  mkdir -p "$(dirname "$restore_path")"
  mv "$backup_file" "$restore_path"
done

sudo fd '.' /root/archie-pre-stow-backup --type f --hidden | while read -r backup_file; do
  relative_path="${backup_file#/root/archie-pre-stow-backup/}"

  case "$relative_path" in
    usr-share-xkeyboard-config-2/*)
      restore_path="/usr/share/xkeyboard-config-2/${relative_path#usr-share-xkeyboard-config-2/}"
      ;;
    *)
      restore_path="/etc/$relative_path"
      ;;
  esac

  sudo mkdir -p "$(dirname "$restore_path")"
  sudo mv "$backup_file" "$restore_path"
done
```

After the restore, verify that the expected pre-migration files are back in
place before retrying the migration.
