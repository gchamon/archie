#cloud-config

hostname: ${ARCHIE_VM_HOSTNAME}
fqdn: ${ARCHIE_VM_HOSTNAME}
package_update: true
package_upgrade: true
ssh_pwauth: false

users:
  - default
  - name: ${ARCHIE_VM_USERNAME}
    groups:
      - wheel
      - seat
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    lock_passwd: false
    hashed_passwd: ${ARCHIE_VM_PASSWORD_HASH}
    ssh_authorized_keys:
      - ${ARCHIE_VM_SSH_AUTHORIZED_KEY}

packages:
  - base-devel
  - git
  - hyprland
  - kitty
  - mesa
  - pipewire
  - seatd
  - sddm
  - sudo
  - waybar
  - xdg-desktop-portal-hyprland
  - openssh

write_files:
  - path: /etc/sddm.conf.d/10-archie-bootstrap.conf
    permissions: "0644"
    content: |
      [General]
      DisplayServer=wayland

      [Wayland]
      CompositorCommand=Hyprland
  - path: /usr/local/bin/archie-bootstrap-finish.sh
    permissions: "0755"
    content: |
      #!/bin/bash
      set -euo pipefail

      mkdir -p /var/log/archie-bootstrap

      cloud-init status > /var/log/archie-bootstrap/cloud-init-status.txt 2>&1 || true
      journalctl -u cloud-init -u cloud-config -u cloud-final -u sddm --no-pager \
        > /var/log/archie-bootstrap/bootstrap-units.txt 2>&1 || true
      systemctl is-enabled sshd > /var/log/archie-bootstrap/sshd-enabled.txt 2>&1 || true
      systemctl is-enabled sddm > /var/log/archie-bootstrap/sddm-enabled.txt 2>&1 || true
      pacman -Q git hyprland openssh sddm > /var/log/archie-bootstrap/package-baseline.txt 2>&1 || true
      ip addr > /var/log/archie-bootstrap/ip-addr.txt 2>&1 || true

runcmd:
  - [ bash, -lc, "getent group seat >/dev/null || groupadd --system seat" ]
  - [ systemctl, enable, sshd.service ]
  - [ systemctl, enable, sddm.service ]
  - [ systemctl, enable, seatd.service ]
  - [ bash, -lc, "/usr/local/bin/archie-bootstrap-finish.sh" ]

final_message: "Archie bootstrap finished for ${ARCHIE_VM_NAME}"
