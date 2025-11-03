# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository contains a complete Arch Linux system configuration for a Hyprland-based desktop environment. It is designed for single-user personal devices and includes comprehensive configurations for window management, shell customization, theming, and development tools.

The system is nicknamed "Archie" and is deployed to `~/.config` on Arch Linux installations.

## Repository Structure

### Core Components

- **`hypr/`**: Hyprland (Wayland compositor) configuration
  - `hyprland.conf`: Main configuration file with keybindings, animations, window rules
  - `config/device.conf`: Device-specific settings (monitors, backlight, input devices)
  - `config/device.dist.conf`: Distribution template for device-specific configs
  - `scripts/`: Utility scripts for session management, screenshots, menus
  - `hyprpaper.conf` / `hyprpaper.dist.conf`: Wallpaper configuration
  - `hyprlock.conf`: Lock screen configuration

- **`nvim/`**: Neovim configuration based on LazyVim (see nvim/CLAUDE.md for details)

- **`.zshrc`**: Zsh shell configuration using oh-my-zsh and powerlevel10k
  - Sources custom aliases and functions from `~/.local/lib/zsh/`
  - Supports multiple p10k themes: `.p10k-{classic,lean,pure,rainbow}.zsh` for terminals, `.p10k-portable.zsh` for tty

- **`waybar/`**: Status bar configuration (config and style.css)

- **`kitty/`**: Terminal emulator configuration

- **`rofi/`**: Application launcher configuration

- **`dunst/`**: Notification daemon configuration (Catppuccin theme)

- **`xkb-customizations/`**: Custom keyboard layouts for multilingual typing
  - `us-br/`: US-intl keyboard with Brazilian Portuguese additions (AltGr+A=Ã, AltGr+C=Ç, AltGr+O=Õ)
  - `00-xkb.hook`: Pacman hook to persist customizations after xkeyboard-config updates

- **`cronjobs/`**: System automation
  - `cron.hourly/yay_pkglist`: Hourly inventory of explicitly installed packages to `/etc/pkglist.txt`

- **`systemd/user/`**: User systemd service symlinks

## Architecture

### Hyprland Configuration Architecture

The Hyprland configuration uses a modular approach:

1. **Main Config** (`hyprland.conf`): Sources `device.conf` first, then defines:
   - Program variables ($terminal, $menu, etc.)
   - Environment variables (cursor, Qt/GTK themes)
   - Visual settings (gaps, borders, animations, decorations)
   - Keybindings (workspace management, window manipulation, screenshots)
   - Auto-start programs (waybar, clipboard management, system tray apps)

2. **Device-Specific Config** (`config/device.conf`): System-dependent settings:
   - `$backlightDevice`: Backlight device name for `brightnessctl` (find with `ls /sys/class/backlight/`)
   - Monitor configuration (resolution, refresh rate, position)
   - Input device settings (keyboard layout, touchpad behavior)
   - GPU device ordering for multi-GPU systems (`AQ_DRM_DEVICES`)
   - Optional: Nvidia environment variables (LIBVA_DRIVER_NAME, __GLX_VENDOR_LIBRARY_NAME)

3. **Scripts** (`scripts/`):
   - `launch-waybar.sh`: Waybar startup
   - `launch-rofi-frece.sh`: Frequency-sorted command launcher using frece
   - `launch-shell-menu.sh`: Shell command menu
   - `confirm-before-exit.sh`: Power management (exit/poweroff/reboot) with confirmation
   - `screenshot/`: Screenshot utilities using grimblast

### Multi-Device Workflow

When deploying to a new device:

1. Clone repo and rsync to `~/.config`
2. Copy `hypr/config/device.dist.conf` to `hypr/config/device.conf`
3. Edit `device.conf` with device-specific values (monitor name, backlight device, keyboard layout)
4. Copy `hypr/hyprpaper.dist.conf` to `hyprpaper.conf` and configure monitor name
5. Reload Hyprland with `hyprctl reload`

This keeps device-specific configs out of version control (via .gitignore) while maintaining distribution templates.

### Backup Strategy

The system uses Borg backup with revision-based archives stored on NAS (see `docs/BACKUP_AND_RESTORE.md`). Key restored items:
- Browser profiles (`.mozilla/`, `.zen/`)
- SSH keys (`.ssh/`)
- Git config (`.gitconfig`)
- OneDrive sync folder
- Custom scripts (`~/Scripts/`)
- Device-specific Hyprland config

Automated backups managed via [gchamon/borg-automated-backups](https://github.com/gchamon/borg-automated-backups).

## Common Commands

### System Installation

```bash
# Install essential packages
yay -S --needed git base-devel

# Install Hyprland environment packages
yay -S --needed hyprland waybar rofi-wayland dunst kitty ranger \
  brightnessctl pamixer blueman kdeconnect grimblast-git cliphist \
  wl-clip-persist hyprlock hyprpaper hyprcursor

# Install shell
yay -S --needed zsh oh-my-zsh-git zsh-theme-powerlevel10k \
  zsh-fast-syntax-highlighting ttf-meslo-nerd

# Deploy configuration
git clone https://github.com/gchamon/archlinux-system-config
rsync -va ~/archlinux-system-config/ ~/.config
rm -rf ~/archlinux-system-config
```

### Configuration Deployment

```bash
# Deploy device-specific Hyprland config
cp ~/.config/hypr/config/device{.dist,}.conf
$EDITOR ~/.config/hypr/config/device.conf
hyprctl reload

# Deploy hyprpaper config
cp ~/.config/hypr/hyprpaper{.dist,}.conf
$EDITOR ~/.config/hypr/hyprpaper.conf

# Deploy zsh config
ln -s ~/.config/.zshrc ~/.zshrc
ln -s ~/.config/.p10k-lean.zsh ~/.p10k.zsh  # or classic/pure/rainbow
ln -s ~/.config/.p10k-portable.zsh ~/.p10k-portable.zsh
chsh -s $(which zsh)

# Deploy keyboard customizations
sudo rsync -va ~/.config/xkb-customizations/us-br/ /usr/share/xkeyboard-config/
sudo cp ~/.config/xkb-customizations/00-xkb.hook /etc/pacman.d/hooks/

# Deploy cronjobs
sudo rsync -va ~/.config/cronjobs/ /etc/
```

### Hyprland Operations

```bash
# Reload Hyprland configuration
hyprctl reload

# Get monitor names
hyprctl monitors

# Check backlight devices
ls /sys/class/backlight/
brightnessctl -l

# Check GPU devices (for multi-GPU setups)
ls /dev/dri/
```

### Development Setup

```bash
# Install development tools (see docs/DEVELOPMENT.md)
yay -S --needed neovim go npm rust pyenv docker docker-compose

# Install virtualization tools
yay -S qemu-desktop libvirt virt-manager incus

# Enable services
sudo systemctl enable --now docker
sudo gpasswd -a $USER docker
systemctl --user enable --now gcr-ssh-agent
```

## Key Customizations

### Keybinding Modifiers

- `$mainMod`: SUPER key (Windows key)
- Workspace switching: SUPER + [0-9]
- Window management: SUPER + SHIFT + arrow keys (swap), SUPER + CTRL + SHIFT + arrow keys (move)
- Screenshots: Print Screen (area), SHIFT + Print Screen (all monitors)
- Session lock: SUPER + L or lid close
- Power menu: SUPER + M (exit), SUPER + SHIFT + M (poweroff), SUPER + CTRL + M (reboot)

### Brightness Control

Uses `brightnessctl` with device specified in `$backlightDevice`:
- SUPER + CTRL + KP_Add (numpad +): Increase brightness 10%
- SUPER + CTRL + KP_Subtract (numpad -): Decrease brightness 10%

For devices requiring ACPI backlight control, add kernel parameter `acpi_backlight=native` to bootloader.

### Clipboard Management

Uses `cliphist` with `wl-clip-persist` for persistent clipboard:
- SUPER + V: Open clipboard history menu
- Stores both text and images
- History cleared on login (exec-once in hyprland.conf)

### Application Menus

Multiple launcher modes accessible via rofi:
- SUPER + R: Application launcher (drun mode)
- SUPER + W: Window switcher
- SUPER + SHIFT + R: Shell command menu (custom script)
- SUPER + CTRL + SHIFT + R: Frequency-sorted terminal command menu (frece)

## Nvidia Multi-GPU Configuration

For systems with Nvidia + integrated GPU (see docs/GUIDE.md section 4.2):

1. Enable nvidia_drm modeset: `echo "options nvidia_drm modeset=1" | sudo tee /etc/modprobe.d/nvidia.conf`
2. Add early kernel modules to `/etc/mkinitcpio.conf`: `MODULES=(... nvidia nvidia_modeset nvidia_uvm nvidia_drm ...)`
3. Run `sudo mkinitcpio -P`
4. Add to `device.conf`:
   ```
   env = LIBVA_DRIVER_NAME,nvidia
   env = __GLX_VENDOR_LIBRARY_NAME,nvidia
   env = AQ_DRM_DEVICES,/dev/dri/card0:/dev/dri/card1
   ```
5. Ensure `bumblebee` is NOT installed (blacklists nvidia_drm)

## External Documentation References

- **Installation Guide**: `docs/GUIDE.md` - Complete system setup from fresh Arch install
- **Development Setup**: `docs/DEVELOPMENT.md` - LazyVim, Docker, Incus, virtualization
- **Backup/Restore**: `docs/BACKUP_AND_RESTORE.md` - Borg-based backup workflow (personal, NAS-dependent)
- **Keyboard Shortcuts**: `docs/KEYBOARD_SHORTCUTS.md` - Complete keybinding reference
- **Keyboard Customizations**: `docs/KEYBOARD_CUSTOMIZATIONS.md` - XKB layout modifications
- **Neovim**: `nvim/CLAUDE.md` - LazyVim configuration architecture
