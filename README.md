# Arch Linux Installation Guide with Hyprland

<!--toc:start-->
- [Arch Linux Installation Guide with Hyprland](#arch-linux-installation-guide-with-hyprland)
  - [1. Initial Setup](#1-initial-setup)
    - [1.1 Install Essential Packages](#11-install-essential-packages)
    - [1.2 Install Yay (AUR Helper)](#12-install-yay-aur-helper)
    - [1.3 Install Packages with Yay](#13-install-packages-with-yay)
  - [2. Deploying system config](#2-deploying-system-config)
    - [2.1 System specific configuration](#21-system-specific-configuration)
  - [3. Theming](#3-theming)
    - [3.1 Install GTK Theme](#31-install-gtk-theme)
    - [3.2 SDDM Theme (Slice 1.5.1)](#32-sddm-theme-slice-151)
  - [4. System Configuration](#4-system-configuration)
    - [4.1 Boot Options](#41-boot-options)
    - [4.2 Key Wallet](#42-key-wallet)
    - [4.3 Systemd Services](#43-systemd-services)
  - [5. Restore from Backup](#5-restore-from-backup)
    - [5.1 Mount Backup Server](#51-mount-backup-server)
    - [5.2 Mount Borg Backup](#52-mount-borg-backup)
    - [5.3 Restore Specific Directories and Files](#53-restore-specific-directories-and-files)
      - [**HOME Directory**](#home-directory)
      - [**System Configuration Files**](#system-configuration-files)
    - [5.4 Change the default shell to zsh](#54-change-the-default-shell-to-zsh)
  - [6. Virtualization Setup](#6-virtualization-setup)
    - [6.1 Install Virtualization Tools](#61-install-virtualization-tools)
    - [6.2 Starting required services](#62-starting-required-services)
<!--toc:end-->

This guide provides step-by-step instructions for installing Arch Linux with Hyprland, including package installation, theming, configuration, and backup restoration.

---

## 1. Initial Setup

### 1.1 Install Essential Packages

```bash
sudo pacman -S --needed git base-devel
```

### 1.2 Install Yay (AUR Helper)

```bash
git clone https://aur.archlinux.org/yay-bin.git
cd yay-bin
makepkg -si
cd ..
rm -rf yay-bin
yay -S yay
yay -Scc
```

### 1.3 Install Packages with Yay

Install the following packages using `yay`:

```bash
yay -S \
  bc \
  bind \
  bitwarden \
  blueman \
  borg \
  cliphist \
  dunst \
  fzf \
  git \
  gnome-keyring \
  gnome-system-monitor \
  go \
  hyprcursor \
  hyprpaper \
  inotify-tools \
  jq \
  kdeconnect \
  lsd \
  neovim \
  nfs-utils \
  noto-fonts \
  noto-fonts-emoji \
  npm \
  plocate \
  pyenv \
  pyfuse3 \
  qt5-graphicaleffects \
  rsync \
  rust \
  rsync \
  seahorse \
  wl-clip-persist \
  xcursor-breeze5 \
  zen-browser-bin \
  zip \
  zsh-fast-syntax-highlighting
```

---

## 2. Deploying system config

Clone this repo and deploy it to `~/.config`

```bash
git clone https://github.com/gchamon/.config ~/config-deploy
rsync -va ~/config-deploy/ ~/.config
rm -rf ~/config-deploy
```

### 2.1 System specific configuration

System specific configurations reside in `~/.config/hypr/config`. To deploy one config, create a symbolic link for it:

```bash
ln -s ~/.config/hypr/config/nitro.conf ~/.config/hypr/config/current.conf
```

If no system specific configuration applies, deploy the empty config:

```bash
ln -s ~/.config/hypr/config/empty.conf ~/.config/hypr/config/current.conf
```

---

## 3. Theming

### 3.1 Install GTK Theme

```bash
yay -S arc-gtk-theme
```

### 3.2 SDDM Theme (Slice 1.5.1)

1. Download the [SDDM Slice theme](https://github.com/EricKotato/sddm-slice/releases/tag/1.5.1).
2. Deploy to SDDM themes directory:

```bash
sudo cp -r path/to/slice /usr/share/sddm/themes/
```

---

## 4. System Configuration

### 4.1 Boot Options

Add the following to your bootloader configuration (e.g., `grub.cfg` or `refind.conf`):

```text
nvidia_drm.modeset=1
```

*(Use this if you're using NVIDIA proprietary drivers, as per the Hyprland master tutorial.)*

### 4.2 Key Wallet

Install `gnome-keyring` for secure passphrase storage:

```bash
yay -S gnome-keyring
```

### 4.3 Systemd Services

Enable and start the following services:

```bash
# User services
for service in gcr-ssh-agent onedrive; do
  systemctl --user enable $service
  systemctl --user start $service
done

# System services
for service in bluetooth; do
  sudo systemctl enable $service
  sudo systemctl start $service
done
```

---

## 5. Restore from Backup

### 5.1 Mount Backup Server

Mount the remote backup server (`192.168.0.5`) to `/media/storage`:

```bash
sudo mount -t nfs 192.168.0.5:/media/storage /media/storage
```

### 5.2 Mount Borg Backup

Mount the Borg archive:

```bash
borg mount /media/storage/borg-backups/nitro/home /path/to/recovery/home
borg mount /media/storage/borg-backups/nitro/etc /path/to/recovery/etc
```

### 5.3 Restore Specific Directories and Files

Use the following `rsync` commands to explicitly restore the listed directories and files:

#### **HOME Directory**

```bash
RECOVERY_PATH=~/recovery-home/home/gchamon
rsync -av $RECOVERY_PATH/.mozilla/ ~/.mozilla/
rsync -av $RECOVERY_PATH/.zen/ ~/.zen/
rsync -av $RECOVERY_PATH/.local/lib/ ~/.local/lib/
rsync -av $RECOVERY_PATH/.ssh/ ~/.ssh/
rsync -av $RECOVERY_PATH/OneDrive/ ~/OneDrive/
rsync -av $RECOVERY_PATH/Scripts/ ~/Scripts/
```

#### **System Configuration Files**

```bash
RECOVERY_PATH=~/recovery-etc/etc
rsync -av $RECOVERY_PATH/pacman.conf /etc/pacman.conf
rsync -av $RECOVERY_PATH/pacman.d/ /etc/pacman.d/
```

### 5.4 Change the default shell to zsh

```bash
chsh -s $(which zsh)
```

---

## 6. Virtualization Setup

### 6.1 Install Virtualization Tools

```bash
yay -S qemu-desktop libvirt virt-manager dnsmasq
```

### 6.2 Starting required services

Once the `~/Scripts` folder is restored from backup you can just:

```bash
~/Scripts/qemu-services.sh
```

---

This guide assumes a clean Arch Linux installation. Adjust paths and configurations as needed for your specific environment.
