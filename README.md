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
    - [3.1 Install Theme files](#31-install-theme-files)
    - [3.2 SDDM Theme (Slice 1.5.1)](#32-sddm-theme-slice-151)
    - [3.3 Install the GTK theme](#33-install-the-gtk-theme)
  - [4. System Configuration](#4-system-configuration)
    - [4.1 Boot Options](#41-boot-options)
    - [4.2 Dependencies](#42-dependencies)
    - [4.3 OneDrive config](#43-onedrive-config)
    - [4.4 Systemd Services](#44-systemd-services)
  - [5. Restore from Backup](#5-restore-from-backup)
    - [5.0 Dependencies](#50-dependencies)
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

### 1.0 Arch post-install notice

After installing archlinux with [archinstall](github.com/archlinux/archinstall)
there can be a problem with decrypting a separate home partition, where
cryptsetup still asks for a password even with a valid decryption key that
`archinstall` creates. The workaround is described in [this
issue](https://github.com/archlinux/archinstall/issues/3583).

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
yay -S --needed \
  bc \
  bind \
  blueman \
  borg \
  cliphist \
  dunst \
  fzf \
  git \
  gnome-system-monitor \
  go \
  hyprcursor \
  hyprpaper \
  inotify-tools \
  jq \
  kdeconnect \
  less \
  lsd \
  ncdu \
  neovim \
  nfs-utils \
  noto-fonts \
  noto-fonts-emoji \
  npm \
  otf-font-awesome \
  pavucontrol \
  plocate \
  pyenv \
  python-pyfuse3 \
  rofi-wayland \
  rsync \
  rust \
  waybar \
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

### 3.1 Install Theme files

```bash
yay -S --needed \
  archlinux-wallpaper \
  gnome-themes-extra \
  qt5-graphicaleffects
```

### 3.2 SDDM Theme (Slice 1.5.1)

Unfortunately the main branch of the slice theme repo isn't compatible with SDDM, making it impossible to just install `sddm-slice-git`.

1. Download the [SDDM Slice theme](https://github.com/EricKotato/sddm-slice/releases/tag/1.5.1).
2. Deploy to SDDM themes directory:

```bash
cd ~/Downloads
tar -xzvf sddm-slice-1.5.1.tar.gz
sudo mv sddm-slice-1.5.1 /usr/share/sddm/themes/slice
```

3. Configure sddm theme:

```bash
cat > /tmp/theme.conf <<EOF
[Theme]
Current=slice
EOF

sudo mkdir -p /etc/sddm.conf.d
sudo mv /tmp/theme.conf /etc/sddm.conf.d
```

### 3.3 Install the GTK theme

1. Install NWG Look

```
yay -S nwg-look
```

2. Configure `Adwaita-dark` in the theme picket. To run the picker, bring up the runner modal with `SUPER+R` and choose `GTK Settings`.

---

## 4. System Configuration

### 4.1 Boot Options

Add the following to your bootloader configuration (e.g., `grub.cfg` or `refind.conf`):

```text
nvidia_drm.modeset=1
```

*(Use this if you're using NVIDIA proprietary drivers, as per the Hyprland master tutorial.)*

### 4.2 Dependencies

```bash
yay -S gnome-keyring onedrive-abraunegg seahorse
```

### 4.3 OneDrive config

```bash
onedrive --sync
```

### 4.4 Systemd Services

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

### 4.5 Cronjobs

Cronjobs are in the `cronjobs/` folder and can be deployed with rsync:

```
sudo rsync -va ./cronjobs/ /etc/
```

---

## 5. Restore from Backup

### 5.0 Dependencies

```bash
yay -S bitwarden
```

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

They will ask for the password which you know where to find. To deploy the password follow the README at [gchamon/borg-automated-backups](github.com/gchamon/borg-automated-backups).

### 5.3 Restore Specific Directories and Files

Use the following `rsync` commands to explicitly restore the listed directories and files:

#### **HOME Directory**

```bash
RECOVERY_PATH=~/recovery-home/home/gchamon
sudo rsync -av $RECOVERY_PATH/.mozilla/ ~/.mozilla/
sudo rsync -av $RECOVERY_PATH/.zen/ ~/.zen/
sudo rsync -av $RECOVERY_PATH/.local/lib/ ~/.local/lib/
sudo rsync -av $RECOVERY_PATH/.ssh/ ~/.ssh/
sudo rsync -av $RECOVERY_PATH/OneDrive/ ~/OneDrive/
sudo rsync -av $RECOVERY_PATH/Scripts/ ~/Scripts/
```

#### **System Configuration Files**

```bash
RECOVERY_PATH=~/recovery-etc/etc
sudo rsync -av $RECOVERY_PATH/pacman.conf /etc/pacman.conf
sudo rsync -av $RECOVERY_PATH/pacman.d/ /etc/pacman.d/
```

### 5.4 Change the default shell to zsh

Zsh shell after restore relies on `oh-my-zsh` and `powerlevel10k`, which will need to be installed:

```bash
yay -S oh-my-zsh-git zsh-theme-powerlevel10k ttf-meslo-nerd
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
