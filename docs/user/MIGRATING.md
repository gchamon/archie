# Archie Migration Guide

<!--toc:start-->

- [Archie Migration Guide](#archie-migration-guide)
  - [v3.0 to v3.1](#v30-to-v31)
    - [Migrating](#migrating)
  - [v2 to v3](#v2-to-v3)
    - [Migrating](#migrating-1)
    - [Restore after a failed migration](#restore-after-a-failed-migration)
<!--toc:end-->

This guide covers migration across Archie releases.

Archie v2 used an `rsync`-based deployment flow. Archie v3 uses GNU Stow and
the `deployment-packages/` layout. Stow can be applied on top of a v2
deployment only after conflicting copied files are moved aside.

## v3.0 to v3.1

In v3.1, several files that were previously created manually from guide snippets
are now managed through Stow packages:

- `~/.config/gtk-3.0/settings.ini`
- `~/.config/gtk-4.0/settings.ini`
- `/etc/sddm.conf.d/theme.conf`
- `/etc/modprobe.d/nvidia.conf`
- `/etc/systemd/logind.conf.d/lid-close.conf`

The files that remain machine-specific and still stay outside Stow management
do not change in this migration:

- `~/.config/hypr/config/device.conf`
- `~/.config/hypr/hyprpaper.conf`
- `~/.local/lib/zsh/overrides.sh`

### Migrating

If you already created any of the newly managed files manually, move those
copies aside before re-stowing:

```bash
mkdir -p "$HOME/archie-pre-stow-backup/.config/gtk-3.0"
mkdir -p "$HOME/archie-pre-stow-backup/.config/gtk-4.0"
sudo mkdir -p /root/archie-pre-stow-backup/sddm.conf.d
sudo mkdir -p /root/archie-pre-stow-backup/modprobe.d
sudo mkdir -p /root/archie-pre-stow-backup/systemd/logind.conf.d

if [[ -e "$HOME/.config/gtk-3.0/settings.ini" && ! -L "$HOME/.config/gtk-3.0/settings.ini" ]]; then
  mv "$HOME/.config/gtk-3.0/settings.ini" "$HOME/archie-pre-stow-backup/.config/gtk-3.0/settings.ini"
fi

if [[ -e "$HOME/.config/gtk-4.0/settings.ini" && ! -L "$HOME/.config/gtk-4.0/settings.ini" ]]; then
  mv "$HOME/.config/gtk-4.0/settings.ini" "$HOME/archie-pre-stow-backup/.config/gtk-4.0/settings.ini"
fi

if sudo test -e /etc/sddm.conf.d/theme.conf && ! sudo test -L /etc/sddm.conf.d/theme.conf; then
  sudo mv /etc/sddm.conf.d/theme.conf /root/archie-pre-stow-backup/sddm.conf.d/theme.conf
fi

if sudo test -e /etc/modprobe.d/nvidia.conf && ! sudo test -L /etc/modprobe.d/nvidia.conf; then
  sudo mv /etc/modprobe.d/nvidia.conf /root/archie-pre-stow-backup/modprobe.d/nvidia.conf
fi

if sudo test -e /etc/systemd/logind.conf.d/lid-close.conf && ! sudo test -L /etc/systemd/logind.conf.d/lid-close.conf; then
  sudo mv /etc/systemd/logind.conf.d/lid-close.conf /root/archie-pre-stow-backup/systemd/logind.conf.d/lid-close.conf
fi
```

Then redeploy the new Stow-managed files:

```bash
stow --dir deployment-packages --target "$HOME/.config" config
sudo stow --dir deployment-packages --target /etc sddm-theme
sudo stow --dir deployment-packages --target /etc lid-close
sudo stow --dir deployment-packages --target /etc nvidia
```

`config` now provides the GTK settings files in addition to the Qt defaults.
`sddm-theme` and `lid-close` are the new default-on `/etc` packages. `nvidia`
is opt-in and should only be redeployed on systems that want Archie's Nvidia
override.

You can also reuse `./scripts/install.sh` to perform this migration. It now
backs up conflicting Stow targets into `~/archie-pre-stow-backup` and
`/root/archie-pre-stow-backup` automatically and honors these toggles:

- `ARCHIE_ENABLE_SDDM_THEME`
- `ARCHIE_ENABLE_LID_CLOSE`
- `ARCHIE_ENABLE_NVIDIA`

## v2 to v3

In v3, the deployment method changed from `rsync` copies to `stow` managed
symlinks.

### Migrating

Choose the `p10k-*` package you want to keep, then back up conflicting paths
based on the actual package contents. This covers `home`, the selected
Powerlevel10k package, `config`, `local`, and the system-level `etc` and
`xkb` packages when the old deployment also copied files into `/etc` or
`/usr/share/xkeyboard-config-2`. The backup flow below skips paths already
managed by Stow symlink trees and only moves an unmanaged leaf path or an
unmanaged symlinked ancestor:

```bash
SELECTED_P10K_PACKAGE="p10k-lean"
mkdir -p "$HOME/archie-pre-stow-backup"

backup_stow_conflicts() {
  local package_dir="$1"
  local deploy_root="$2"
  local backup_root="$3"
  declare -A handled_conflicts=()

  find_conflicting_deployed_path() {
    local deploy_root="$1"
    local deployed_path="$2"
    local current_path=""

    if [[ -L "$deployed_path" ]]; then
      printf '%s\n' "$deployed_path"
      return 0
    fi

    current_path="$(dirname "$deployed_path")"
    while [[ "$current_path" != "$deploy_root" ]]; do
      if [[ -L "$current_path" ]]; then
        printf '%s\n' "$current_path"
        return 0
      fi

      current_path="$(dirname "$current_path")"
    done

    if [[ -e "$deployed_path" ]]; then
      printf '%s\n' "$deployed_path"
      return 0
    fi

    return 1
  }

  is_managed_deployed_path() {
    local deploy_root="$1"
    local package_dir="$2"
    local conflicting_path="$3"
    local relative_conflict_path="${conflicting_path#"$deploy_root"/}"
    local managed_target="$package_dir/$relative_conflict_path"

    [[ -L "$conflicting_path" ]] || return 1
    [[ -e "$managed_target" || -L "$managed_target" ]] || return 1
    [[ "$(readlink -f "$conflicting_path")" == "$(readlink -f "$managed_target")" ]]
  }

  fd '.' "$package_dir" --type f --hidden | while read -r file_to_deploy; do
    relative_path="${file_to_deploy#"$package_dir"/}"
    deployed_path="$deploy_root/$relative_path"

    conflicting_path="$(find_conflicting_deployed_path "$deploy_root" "$deployed_path")" || continue

    if [[ -n "${handled_conflicts[$conflicting_path]:-}" ]]; then
      continue
    fi

    handled_conflicts["$conflicting_path"]=1

    if is_managed_deployed_path "$deploy_root" "$package_dir" "$conflicting_path"; then
      continue
    fi

    backup_path="$backup_root/${conflicting_path#"$deploy_root"/}"
    mkdir -p "$(dirname "$backup_path")"
    mv "$conflicting_path" "$backup_path"
  done
}

backup_stow_conflicts_sudo() {
  local package_dir="$1"
  local deploy_root="$2"
  local backup_root="$3"
  declare -A handled_conflicts=()

  find_conflicting_deployed_path() {
    local deploy_root="$1"
    local deployed_path="$2"
    local current_path=""

    if sudo test -L "$deployed_path"; then
      printf '%s\n' "$deployed_path"
      return 0
    fi

    current_path="$(dirname "$deployed_path")"
    while [[ "$current_path" != "$deploy_root" ]]; do
      if sudo test -L "$current_path"; then
        printf '%s\n' "$current_path"
        return 0
      fi

      current_path="$(dirname "$current_path")"
    done

    if sudo test -e "$deployed_path"; then
      printf '%s\n' "$deployed_path"
      return 0
    fi

    return 1
  }

  is_managed_deployed_path() {
    local deploy_root="$1"
    local package_dir="$2"
    local conflicting_path="$3"
    local relative_conflict_path="${conflicting_path#"$deploy_root"/}"
    local managed_target="$package_dir/$relative_conflict_path"

    sudo test -L "$conflicting_path" || return 1
    [[ -e "$managed_target" || -L "$managed_target" ]] || return 1
    [[ "$(readlink -f "$conflicting_path")" == "$(readlink -f "$managed_target")" ]]
  }

  sudo fd '.' "$package_dir" --type f --hidden | while read -r file_to_deploy; do
    relative_path="${file_to_deploy#"$package_dir"/}"
    deployed_path="$deploy_root/$relative_path"

    conflicting_path="$(find_conflicting_deployed_path "$deploy_root" "$deployed_path")" || continue

    if [[ -n "${handled_conflicts[$conflicting_path]:-}" ]]; then
      continue
    fi

    handled_conflicts["$conflicting_path"]=1

    if is_managed_deployed_path "$deploy_root" "$package_dir" "$conflicting_path"; then
      continue
    fi

    backup_path="$backup_root/${conflicting_path#"$deploy_root"/}"
    sudo mkdir -p "$(dirname "$backup_path")"
    sudo mv "$conflicting_path" "$backup_path"
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

After the conflicting copied paths have been moved aside, deploy Archie v3:

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
[`docs/user/GUIDE.md`](./GUIDE.md), including the machine-specific `.dist`-derived
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

Restore the backed-up home, XDG, local library and system paths:

```bash
fd '.' "$HOME/archie-pre-stow-backup" --type f --type l --hidden | while read -r backup_file; do
  relative_path="${backup_file#"$HOME/archie-pre-stow-backup"/}"
  restore_path="$HOME/$relative_path"

  mkdir -p "$(dirname "$restore_path")"
  mv "$backup_file" "$restore_path"
done

sudo fd '.' /root/archie-pre-stow-backup --type f --type l --hidden | while read -r backup_file; do
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
