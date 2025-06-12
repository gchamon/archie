# Arch Linux Installation Guide with Hyprland

<!--toc:start-->
- [Arch Linux Installation Guide with Hyprland](#arch-linux-installation-guide-with-hyprland)
  - [1. Initial Setup](#1-initial-setup)
    - [1.0 Installing Arch Linux](#10-installing-arch-linux)
    - [1.1 Install Essential Packages](#11-install-essential-packages)
    - [1.2 Install Yay (AUR Helper)](#12-install-yay-aur-helper)
    - [1.3 Install Packages with Yay](#13-install-packages-with-yay)
  - [2. Deploying system config](#2-deploying-system-config)
    - [2.1 System specific configuration](#21-system-specific-configuration)
    - [2.2 Deploy oh-my-zsh](#22-deploy-oh-my-zsh)
    - [2.3 Add required home folders](#23-add-required-home-folders)
  - [3. Theming](#3-theming)
    - [3.1 Install Theme files](#31-install-theme-files)
    - [3.2 SDDM Theme (Slice 1.5.1)](#32-sddm-theme-slice-151)
    - [3.3 Install the GTK theme](#33-install-the-gtk-theme)
  - [4. System Configuration](#4-system-configuration)
    - [4.1 Boot Options](#41-boot-options)
    - [4.2 Dependencies](#42-dependencies)
    - [4.4 Systemd Services](#44-systemd-services)
    - [4.5 Cronjobs](#45-cronjobs)
  - [5. Backup and Restore](#5-backup-and-restore)
<!--toc:end-->

This guide provides step-by-step instructions for deploying Hyprland to an Arch Linux installation, including package installation, theming, configuration, and backup restoration.

Up to section [4. System Configuration](#4-system-configuration) the guide is supposed to be system and backup agnostic and should work in any system.

![desktop](docs/assets/desktop.png)
![windows](docs/assets/windows-opened.png)

Credits to
[cjbassi](https://github.com/cjbassi/config/tree/master/.config/waybar) for the
[waybar](https://github.com/Alexays/Waybar) theme.

Credits to [catppuccin/dunst](https://github.com/catppuccin/dunst) for the
[dunst](https://github.com/dunst-project/dunst) theme.

Credits to [EricKotato/sddm-slice](https://github.com/EricKotato/sddm-slice)
for the [sddm](https://github.com/sddm/sddm) theme.

Credits to
[connorholyday/kitty-snazzy](https://github.com/connorholyday/kitty-snazzy) for
the [kitty](https://github.com/kovidgoyal/kitty) theme.

 GTK theme is Adwaita-dark. [Oh-my-zsh](https://github.com/ohmyzsh/ohmyzsh/)
 theme is [powerlevel10k](https://github.com/romkatv/powerlevel10k).

Special thanks to [Arch Linux](https://archlinux.org/) team and the folks behind
[Hyprland](https://hypr.land/).

---

## 1. Initial Setup

### 1.0 Installing Arch Linux

This guide isn't prescriptive about how to install Arch Linux, but it requires
the installation of the desktop profile with hyprland when using
[archinstall](https://github.com/archlinux/archinstall).

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
  cliphist \
  dunst \
  fzf \
  git \
  gnome-system-monitor \
  go \
  grimblast-git \
  hyprcursor \
  hyprlock \
  hyprpaper \
  inotify-tools \
  jq \
  kdeconnect \
  ksnip \
  less \
  lsd \
  ncdu \
  neovim \
  noto-fonts \
  noto-fonts-emoji \
  npm \
  otf-font-awesome \
  pavucontrol \
  plocate \
  pyenv \
  rofi-wayland \
  rsync \
  rust \
  unzip \
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
git clone https://github.com/gchamon/archlinux-system-config
rsync -va ~/archlinux-system-config/ ~/.config
rm -rf ~/archlinux-system-config
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

### 2.2 Deploy oh-my-zsh

Zsh shell relies on `oh-my-zsh` and `powerlevel10k`, which will need to be installed:

```bash
yay -S oh-my-zsh-git zsh-theme-powerlevel10k ttf-meslo-nerd
test -f ~/.zshrc && mv ~/.zshrc{,.bk}
ln -s ~/.config/.zshrc ~/.zshrc
```

There are four preconfigured powerlevel10k prompt styles. Choose one of
`.p10k-classic.zsh`, `.p10k-lean.zsh`, `.p10k-pure.zsh` or `.p10k-rainbow.zsh`
and create a symbolic link to `~/.p10k.zsh`:

```bash
ln -s ~/.config/.p10k-classic.zsh ~/.p10k.zsh
```

There is a fifth powerlevel10k prompt style that is geared towards supporting
tty shells, which is called `.p10k-portable.zsh` and it should be deployed to
the home folder along with the chosen profile:

```bash
ln -s ~/.config/.p10k-portable.zsh ~/.p10k-portable.zsh
```

Now change the shell to if necessary:

```bash
chsh -s $(which zsh)
```

### 2.3 Add required home folders

This is for the screenshot utility to work.

```bash
mkdir -p ~/Pictures/Screenshots
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

Unfortunately the main branch of the slice theme repo isn't compatible with
SDDM, making it impossible to just install `sddm-slice-git`. You must download
and extract the tar archive related to the [v1.5.1
release](https://github.com/EricKotato/sddm-slice/releases/tag/1.5.1) and
deploy it to `/usr/share/sddm/themes/slice` manually.

1. Download the [SDDM Slice theme v1.5.1](https://github.com/EricKotato/sddm-slice/releases/tag/1.5.1).
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
yay -S gnome-keyring seahorse
```

### 4.4 Systemd Services

Enable and start the following services:

```bash
# User services
for service in gcr-ssh-agent; do
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

Current cronjobs are:

| Cronjob                 | Description                                                                                        |
|-------------------------|----------------------------------------------------------------------------------------------------|
| cron.hourly/yay_pkglist | Takes an inventory of the packages manually installed with yay and writes it to `/etc/pkglist.txt` |

---

## 5. Backup and Restore

The [Backup and Restore](BACKUP_AND_RESTORE.md) guide isn't intended to be
generally applicable outside my personal environment. It's there for my
personal disaster recovery drills, but could inspire others looking for backup
strategies.
