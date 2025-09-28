# Arch Linux system configuration guide

<!--toc:start-->
- [Arch Linux system configuration guide](#arch-linux-system-configuration-guide)
  - [1. Initial Setup](#1-initial-setup)
    - [1.0 Installing Arch Linux](#10-installing-arch-linux)
    - [1.1 Install Essential Packages](#11-install-essential-packages)
    - [1.2 Install Yay (AUR Helper)](#12-install-yay-aur-helper)
    - [1.3 Install Essential Packages with Yay](#13-install-essential-packages-with-yay)
    - [1.3 Install Development Packages for LazyVim](#13-install-development-packages-for-lazyvim)
  - [2. Deploying system config](#2-deploying-system-config)
    - [2.1 System specific configuration](#21-system-specific-configuration)
      - [Customization of device-specific configs](#customization-of-device-specific-configs)
    - [2.2 Deploy oh-my-zsh](#22-deploy-oh-my-zsh)
    - [2.3 Add required home folders](#23-add-required-home-folders)
  - [3. Theming](#3-theming)
    - [3.1 Install Theme Packages](#31-install-theme-packages)
    - [3.2 SDDM Theme (Slice 1.5.1)](#32-sddm-theme-slice-151)
    - [3.3 Install the GTK theme](#33-install-the-gtk-theme)
  - [4. System Configuration](#4-system-configuration)
    - [4.1 Boot Options](#41-boot-options)
      - [ACPI Backlight control](#acpi-backlight-control)
    - [4.2 Nvidia](#42-nvidia)
      - [Bumblebee](#bumblebee)
    - [4.3 Hibernate on lid close](#43-hibernate-on-lid-close)
      - [External monitor frozen after return from sleep](#external-monitor-frozen-after-return-from-sleep)
    - [4.4 Keyring](#44-keyring)
    - [4.5 Systemd Services](#45-systemd-services)
    - [4.6 Cronjobs](#46-cronjobs)
  - [5. Further reading](#5-further-reading)
    - [5.1 Keyboard shortcuts](#51-keyboard-shortcuts)
    - [5.2 Keyboard customizations](#52-keyboard-customizations)
    - [5.3 Backup and Restore](#53-backup-and-restore)
    - [5.4 Development](#54-development)
<!--toc:end-->

This guide provides step-by-step instructions for deploying Hyprland to an Arch
Linux installation, including package installation, theming, configuration, and
backup restoration.

This is intended for single user devices, personal devices that aren't going to
be shared by multiple linux users.

Up to section [4. System Configuration](#4-system-configuration) the guide is
supposed to be system and backup agnostic and should work in any system.


---

## 1. Initial Setup

### 1.0 Installing Arch Linux

This guide isn't prescriptive about how to install Arch Linux, but it requires
the installation of the desktop profile with hyprland by using
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

### 1.3 Install Essential Packages with Yay

Install the following packages using `yay`:

```bash
yay -S --needed \
  acpi \
  bc \
  bind \
  blueman \
  brightnessctl \
  calibre \
  cliphist \
  dunst \
  fd \
  frece \
  fzf \
  gnome-system-monitor \
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
  man-db \
  ncdu \
  noto-fonts \
  noto-fonts-emoji \
  otf-font-awesome \
  pamixer \
  pavucontrol \
  plocate \
  ranger \
  rofi-wayland \
  rsync \
  unzip \
  waybar \
  wl-clip-persist \
  xorg-xhost \
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

System specific configurations reside in `~/.config/hypr/config`. To deploy the
configuration, copy the default distribution file and change it:

```bash
cp ~/.config/hypr/config/device.dist.conf ~/.config/hypr/config/device.conf
${EDITOR:-nvim} ~/.config/hypr/config/device.conf
hyprctl reload
```

`hyprpaper` also needs to be aware of the internal monitor name, which can vary between devices. To configure `hyprpaper`:

```bash
cp ~/.config/hypr/hyprpaper.dist.conf ~/.config/hyprpaper.conf
${EDITOR:-nvim} ~/.config/hypr/hyprpaper.conf
```

#### Customization of device-specific configs

For `brightnessctl` to work, use `$backlightDevice` to configure which device
`brightnessctl` should use to control brightness.

To get a list of the available devices, run:

```bash
ls -1 /sys/class/backlight/
```

You can also run `brightnessctl -l` and check which device is related to the
internal GPU. In my case:

```text
$ brightnessctl -l
# ...
Device 'amdgpu_bl1' of class 'backlight':
 Current brightness: 181 (71%)
 Max brightness: 255
# ...
```

The name of the device is related to which card it's linked to in `/dev/dri`.

If none is available, you should try using `linux-lts` kernel and play around
with `acpi_backlight` kernel parameter. For more information see [ACPI
backlight control](#acpi-backlight-control) and archlinux docs on [Backlight's
kernel command-line
options](https://wiki.archlinux.org/title/Backlight#Kernel_command-line_options).

### 2.2 Deploy oh-my-zsh

Zsh shell relies on `oh-my-zsh` and `powerlevel10k`, which will need to be installed:

```bash
yay -S --needed \
  zsh \
  zsh-completions \
  oh-my-zsh-git \
  zsh-theme-powerlevel10k \
  ttf-meslo-nerd

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

Now change the shell to `zsh` if necessary:

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

### 3.1 Install Theme Packages

```bash
yay -S --needed \
  archlinux-wallpaper \
  gnome-themes-extra \
  qt5-graphicaleffects \
  xcursor-breeze5
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

These are options that need to be passed to the kernel at boot time. See the
bootloader docs for information on how to add these options.

For systemd-boot, which I use, they are located at `/boot/loader/entries/`. One
of the entries is the fallback, which should be left untouched.

#### ACPI Backlight control

For my Acer Nitro notebook, I need to add the following boot option so I can
control the device's built-in screen brightness with `brightnessctl`:

```
acpi_backlight=native
```

### 4.2 Nvidia

Currently using `nvidia-open-dkms` without issues.

From [Hyprland Nvidia](https://wiki.hypr.land/Nvidia/), enable modeset for nvidia_drm:

```bash
echo "options nvidia_drm modeset=1" | tee /etc/modprobe.d/nvidia.conf
```

This can also be set via kernel boot parameter `nvidia_drm.modeset=1`. In my
testing, using the former makes the Nvidia GPU attach to `/dev/dri/card0`,
while the latter makes it attach to `/dev/dri/card0`. This influences where the
internal GPU is mapped, which in turn affects the name of the device used to
control the backlight.

In `/etc/mkinitcpio.conf` add the required Nvidia kernel modules for [early
loading](https://wiki.archlinux.org/title/Kernel_module#Early_module_loading):

```
MODULES=(... nvidia nvidia_modeset nvidia_uvm nvidia_drm ...)
```

After which you must run `sudo mkinitcpio -P`.

Lastly, add the required environment variables to the hyprland config for the
device under `~/.config/hypr/config/device.conf`:

```hyprland
env = LIBVA_DRIVER_NAME,nvidia
env = __GLX_VENDOR_LIBRARY_NAME,nvidia
```

For dual monitors, you should also follow (Hyprland
Multi-GPU)[https://wiki.hypr.land/Configuring/Multi-GPU/] guide to check
which device your internal and external GPU is linked to and set them properly.

#### Bumblebee

Before recent updates, it was OK to have bumblebee installed, but now, due to a
rule it deploys in `/usr/lib/modprobe.d/bumblebee.conf` it blacklists among
other kernel modules, the `nvidia_drm` module, which disables external
monitors. So it's important to make sure that `bumblebee` isn't installed in
the system.

### 4.3 Hibernate on lid close

By default, systemd handles ACPI events via default rules which are documented
in archlinux's [Power management > ACPI
events](https://wiki.archlinux.org/title/Power_management#ACPI_events).

To make it so that every lid close event will put the machine in hybrid sleep:

```bash
sudo mkdir -p /etc/systemd/logind.conf.d
sudo tee /etc/systemd/logind.conf.d/lid-close.conf <<CONF
[Login]
HandleLidSwitch=hybrid-sleep
HandleLidSwitchDocked=hybrid-sleep
HandleLidSwitchExternalPower=hybrid-sleep
CONF
```

#### External monitor frozen after return from sleep

Sometimes when the system returns from sleep, the second monitor will freeze
and won't respond to updates. This happens when the HDMI output is connected to
a different GPU than the built-in display. That seems to happen, however, when
returning from sleep right after putting it to sleep, maybe because the
external monitor didn't have time to enter power saving mode. This is
apparently a [common](https://github.com/hyprwm/Hyprland/issues/9194)
[issue](https://old.reddit.com/r/hyprland/comments/1jdcpkd/external_monitor_has_its_display_output_frozen/)
in hyprland and maybe not even hyprland's fault.

In any case, until a better solution is found, the workaround is to execute
`hyprctl reload` to bring the second screen back to life. In my case I have to
run it twice, so it picks up the right resolution for the screen.

### 4.4 Keyring

This enables the system to store password for commonly used credentials that
are password protected, like ssh keys.

```bash
yay -S gnome-keyring seahorse
```

### 4.5 Systemd Services

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

### 4.6 Cronjobs

Cronjobs are in the `cronjobs/` folder and can be deployed with rsync:

```
sudo rsync -va ~/.config/cronjobs/ /etc/
```

Current cronjobs are:

| Cronjob                 | Description                                                                                        |
|-------------------------|----------------------------------------------------------------------------------------------------|
| cron.hourly/yay_pkglist | Takes an inventory of the packages manually installed with yay and writes it to `/etc/pkglist.txt` |

---

## 5. Further reading

These are documents that expand the documentation on this desktop environment

### 5.1 Keyboard shortcuts

[Keyboard shortcuts](KEYBOARD_SHORTCUTS.md) documents all the possible keyboard
shortcuts. The information is extracted from hyprland configuration using
[Google's Gemini LLM](https://gemini.google.com).

### 5.2 Keyboard customizations

[Keyboard customizations](KEYBOARD_CUSTOMIZATIONS.md) documents the deployment
of xkeyboard-config compatible customizations that makes it easier to type in a
different language than that of the keyboard in use.

### 5.3 Backup and Restore

The [Backup and Restore](BACKUP_AND_RESTORE.md) guide isn't intended to be
generally applicable outside my personal environment. It's there for my
personal disaster recovery drills, but could inspire others looking for backup
strategies.

### 5.4 Development

[This document](DEVELOPMENT.md) explains steps to install and configure
tools I need for daily work as a developer.
