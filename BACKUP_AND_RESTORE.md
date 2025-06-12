# Backup and Restore

This file contains instructions that are tightly coupled with my backup
strategy and can't be easily distributed. This can serve as a reference or
inspiration for others to follow similar backup strategies, but this is a much
more personal guide, not intended to be generally usable.

<!--toc:start-->
- [1. Restore from Backup](#1-restore-from-backup)
  - [1.1 Dependencies](#11-dependencies)
  - [1.2 Mount Borg Backup](#12-mount-borg-backup)
  - [1.3. Deploy automatic backups](#13-deploy-automatic-backups)
  - [1.4 OneDrive config](#14-onedrive-config)
- [2. Virtualization Setup](#2-virtualization-setup)
  - [2.1 Install Virtualization Tools](#21-install-virtualization-tools)
  - [2.2 Starting required services](#22-starting-required-services)
<!--toc:end-->

## 1. Restore from Backup

### 1.1 Dependencies

Install dependencies and add mountpoints in `/etc/fstab` for the NAS:

```bash
yay -S bitwarden borg python-pyfuse3 nfs-utils

sudo mkdir -p /media/storage /media/fast-storage

sudo cat >> /etc/fstab <<EOF
# NAS
192.168.0.5:/media/storage /media/storage  nfs defaults,soft,timeo=30 0 0
192.168.0.5:/media/fast-storage /media/fast-storage nfs defaults,soft,timeo=30 0 0
EOF

sudo systemctl daemon-reload
sudo mount -a
```

### 1.2 Mount Borg Backup

1. Deploy the password following the README at [gchamon/borg-automated-backups](https://github.com/gchamon/borg-automated-backups).

2. Mount the Borg archives:

First specify the backup and restore paths:

```bash
BORG_BACKUP_PATH=/media/storage/borg-backups/nitro-rev1
RECOVERY_PATH_HOME=$HOME/recovery-home
RECOVERY_PATH_ETC=$HOME/recovery-etc
```

Then mount the latest archives:

```bash
HOME_LATEST_ARCHIVE=$(sudo borg list $BORG_BACKUP_PATH/home --json | jq -r '.archives[-1].archive')
ETC_LATEST_ARCHIVE=$(sudo borg list $BORG_BACKUP_PATH/etc --json | jq -r '.archives[-1].archive')

mkdir -p $RECOVERY_PATH_HOME $RECOVERY_PATH_ETC

sudo borg mount $BORG_BACKUP_PATH/home::$HOME_LATEST_ARCHIVE $RECOVERY_PATH_HOME
sudo borg mount $BORG_BACKUP_PATH/etc::$ETC_LATEST_ARCHIVE $RECOVERY_PATH_ETC
```

3. Restore Specific Directories and Files

Use the following `rsync` commands to explicitly restore the listed directories and files:

  3.1. HOME Directory

```bash
sudo rsync -av {$RECOVERY_PATH_HOME/home,~}/.mozilla/
sudo rsync -av {$RECOVERY_PATH_HOME/home,~}/.zen/
sudo rsync -av {$RECOVERY_PATH_HOME/home,~}/.local/lib/
sudo rsync -av {$RECOVERY_PATH_HOME/home,~}/.ssh/
sudo rsync -av {$RECOVERY_PATH_HOME/home,~}/OneDrive/
sudo rsync -av {$RECOVERY_PATH_HOME/home,~}/Scripts/
sudo rsync -av {$RECOVERY_PATH_HOME/home,~}/.zshenv
```

  3.2. System Configuration Files

```bash
sudo rsync -av {$RECOVERY_PATH_ETC/etc,/etc}/pacman.conf
sudo rsync -av {$RECOVERY_PATH_ETC/etc,/etc}/pacman.d/
```

  3.3. Remove restoration mountpoints

```bash
sudo umount $RECOVERY_PATH_HOME
sudo umount $RECOVERY_PATH_ETC
sudo rm -rf $RECOVERY_PATH_HOME $RECOVERY_PATH_ETC
```

### 1.3. Deploy automatic backups

Use [gchamon/borg-automated-backups](https://github.com/gchamon/borg-automated-backups)
to redeploy the backup automation. Make sure to increment the `revX` in the
backup, for instance, we used in the example `nitro-rev1`, therefore the next
backup deployment should be `nitro-rev2` after a fresh install. This is so that
I avoid erasing data from previous revisions, which frees me to do lean fresh
installs without risking losing data.

### 1.4 OneDrive config

Install [abraunegg's onedrive client](https://github.com/abraunegg/onedrive) for linux:

```bash
onedrive-abraunegg 
```

Sync to authenticate:

```bash
onedrive --sync
```

Then start the service:

```bash
systemctl --user enable onedrive
systemctl --user start onedrive
```

---
