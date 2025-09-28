# Containers and Virtual Machines

I aim to document the required configuration to have docker and other forms of
containerization and virtualization running.


<!--toc:start-->
- [Containers and Virtual Machines](#containers-and-virtual-machines)
    - [LazyVim](#lazyvim)
  - [Git config](#git-config)
  - [Docker install](#docker-install)
  - [Virtualization Setup](#virtualization-setup)
    - [Install Virtualization Tools](#install-virtualization-tools)
    - [Starting required services](#starting-required-services)
  - [Incus install](#incus-install)
<!--toc:end-->

### LazyVim

Install these language-specific packages:

```bash
yay -S --needed \
  go \
  neovim \
  npm \
  pyenv \
  rust
```

[Install nix](https://nixos.org/download/#nix-install-linux) in single user mode:

```bash
sh <(curl --proto '=https' --tlsv1.2 -L https://nixos.org/nix/install) --no-daemon
```

It's more convenient to install from nix official scripts than with arch native
package manager to avoid permission issues in neovim.

In LazyVim, `:LazyExtras` then install `mini-surround`.

## Git config

Git configuration should be restored from [Backup and
Restore](BACKUP_AND_RESTORE.md) procedure, but the configuration is done so
that merge strategy and git signing using ssh key is configured:

- Configure email and name
- Set rebase to false (default strategy merge)
- Set default branch to main
- Configure `git-signing-key` as a signing key following [this
  doc](https://docs.gitlab.com/user/project/repository/signed_commits/ssh/).

## Docker install

```bash
yay -S docker docker-buildx
sudo systemctl enable docker
sudo systemctl start docker
sudo gpasswd -a $USER docker
```

## Virtualization Setup

### Install Virtualization Tools

```bash
yay -S qemu-desktop libvirt virt-manager dnsmasq
```

### Starting required services

Once the `~/Scripts` folder is restored from backup you can just:

```bash
~/Scripts/qemu-services.sh
```

To stop these services:

```bash
~/Scripts/qemu-services.sh stop
```

## Incus install

```bash
yay -S incus
sudo gpasswd -a $USER incus-admin
newgrp incus
cat > /tmp/incus-config.yml <<EOF
config:
  core.https_address: '[::]:8443'
networks:
- config:
    ipv4.address: 10.156.38.1/24
    ipv4.nat: "true"
    ipv6.address: fd42:245c:baca:7c6::1/64
    ipv6.nat: "true"
  description: ""
  name: incusbr0
  type: bridge
  project: default
storage_pools:
- config:
    source: /var/lib/incus/storage-pools/default
  description: ""
  name: default
  driver: dir
storage_volumes: []
profiles:
- config: {}
  description: Default Incus profile
  devices:
    eth0:
      name: eth0
      network: incusbr0
      type: nic
    root:
      path: /
      pool: default
      type: disk
  name: default
  project: ""
projects:
- config:
    features.images: "true"
    features.networks: "true"
    features.networks.zones: "true"
    features.profiles: "true"
    features.storage.buckets: "true"
    features.storage.volumes: "true"
  description: Default Incus project
  name: default
certificates: []
EOF

incus admin init --preseed /tmp/incus-config.yml
```

