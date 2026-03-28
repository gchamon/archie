# Reproducible Environment

This guide defines the first reproducible Archie development environment: an
Incus-managed Arch Linux VM bootstrapped by cloud-init to a graphical-ready
baseline for manual Archie testing.

## Scope

This phase standardizes VM bootstrap only. It does not try to automate full
Archie deployment inside the guest yet.

The reproducible guarantees in this phase are:

- the base image comes from the Incus `images:` remote using the Arch cloud
  alias `images:archlinux/current/cloud`, unless explicitly overridden
- cloud-init input files are rendered from repo-owned templates before instance
  creation
- the guest baseline includes networking, `git`, Hyprland, SDDM, and enough
  packages to begin manual Archie validation
- SSH access is bootstrapped with the host public key from `~/.ssh/homelab.pub`
- bootstrap diagnostics are collected separately from later Archie deployment
  or session issues

The following are intentionally still manual in this phase:

- cloning Archie inside the guest
- installing Archie-specific packages not required for the bootstrap baseline
- running Stow deployment
- machine-specific local file decisions such as `device.conf` values

## Prerequisites

Install and initialize Incus on the host first. The existing baseline is in
[DEVELOPMENT.md](DEVELOPMENT.md#incus-install).

The bootstrap workflow expects:

- `incus`
- `envsubst`
- `ssh`

## Creating a reproducible image

The canonical interface is the Incus CLI itself. This guide intentionally shows
only one happy-path example workflow and leaves the rest to standard Incus
commands and the official docs.

### 1. Render cloud-init inputs

```bash
export ARCHIE_VM_NAME="archie-dev"
export ARCHIE_VM_HOSTNAME="archie-dev"
export ARCHIE_VM_USERNAME="archie"
export ARCHIE_VM_PASSWORD_HASH="$(openssl passwd -6 'archie')"
export ARCHIE_VM_SSH_AUTHORIZED_KEY="$(< ~/.ssh/homelab.pub)"

state_dir=".state/reproducible-environment/${ARCHIE_VM_NAME}"
mkdir -p "${state_dir}"

envsubst < templates/reproducible-environment/cloud-init/user-data.yaml.tpl \
  > "${state_dir}/user-data.yaml"
```

### 2. Create and start the VM with Incus

```bash
incus init images:archlinux/current/cloud "${ARCHIE_VM_NAME}" --vm \
  --config limits.cpu=4 \
  --config limits.memory=8GiB

incus config set "${ARCHIE_VM_NAME}" cloud-init.user-data - < "${state_dir}/user-data.yaml"
incus config device override "${ARCHIE_VM_NAME}" root size=32GiB

incus start "${ARCHIE_VM_NAME}"
```

### 3. Wait for cloud-init to finish

Wait for bootstrap to finish:

```bash
incus exec "${ARCHIE_VM_NAME}" -- cloud-init status --wait
```

Then stop the machine

```bash
incus stop "${ARCHIE_VM_NAME}"
```

### 4. Publish the reproducible image

Once the guest has reached the post-bootstrap state you want to reuse, stop the
VM and publish it into the local Incus image store.

Recommended pre-publish checks:

- remove or archive transient guest-side artifacts you do not want clones to inherit
- confirm the guest is in the exact baseline state you want to capture
- stop the instance cleanly before publishing

Publish the stopped VM into the local Incus image store:

```bash
export ARCHIE_IMAGE_ALIAS="archie/reproducible-baseline"

incus publish "${ARCHIE_VM_NAME}" \
  --alias "${ARCHIE_IMAGE_ALIAS}" \
  --reuse \
  archie.base_image=images:archlinux/current/cloud
```

By default that publishes a private image with the alias
`archie/reproducible-baseline` and replaces any existing image for that alias.

Useful options:

```bash
incus publish "${ARCHIE_VM_NAME}" \
  --alias "${ARCHIE_IMAGE_ALIAS}" \
  --reuse \
  --expire "2026-04-27T00:00:00Z" \
  archie.base_image=images:archlinux/current/cloud \
  description="Archie post-cloud-init baseline"
```

If you need a file-based VM artifact after publishing, export the image bundle:

```bash
incus image export "${ARCHIE_IMAGE_ALIAS}" \
  ".state/reproducible-environment/archie-reproducible-baseline" \
  --vm
```

That produces a portable Incus VM image bundle alongside the local image alias.

## Launching an Archie instance from the reproducible image

Define a new instance name for launches from the captured image:

```bash
export ARCHIE_IMAGE_ALIAS="archie/reproducible-baseline"
export ARCHIE_IMAGE_INSTANCE_NAME="archie-dev-from-image"
export ARCHIE_REPO_URL="https://gitlab.com/gabriel.chamon/archie.git"

envsubst < templates/reproducible-environment/cloud-init/archie-instance-user-data.yaml.tpl \
  > "${state_dir}/archie-instance-user-data.yaml"
```

### 1. Create and start a VM from the published image

```bash
incus init "${ARCHIE_IMAGE_ALIAS}" "${ARCHIE_IMAGE_INSTANCE_NAME}" --vm
incus config set "${ARCHIE_IMAGE_INSTANCE_NAME}" cloud-init.user-data - \
  < "${state_dir}/archie-instance-user-data.yaml"
incus start "${ARCHIE_IMAGE_INSTANCE_NAME}"
incus exec "${ARCHIE_IMAGE_INSTANCE_NAME}" -- cloud-init status --wait
```

That launch-time cloud-init writes `~/pull-archie-repo.sh` for
`${ARCHIE_VM_USERNAME}` so the Archie repo can be cloned or updated on demand
inside the instance.

## Runtime Inputs

The example flow standardizes these runtime inputs:

- `ARCHIE_VM_NAME`: Incus instance name and rendered file directory key
- `ARCHIE_IMAGE_ALIAS`: published Incus image alias reused for new VMs
- `ARCHIE_IMAGE_INSTANCE_NAME`: launched VM name created from the published image
- `ARCHIE_REPO_URL`: Archie repository URL used by `~/pull-archie-repo.sh`
- `ARCHIE_VM_HOSTNAME`: guest hostname
- `ARCHIE_VM_USERNAME`: primary guest user for later Archie work
- `ARCHIE_VM_PASSWORD_HASH`: SHA-512 password hash for local SDDM and console login
- `ARCHIE_VM_SSH_AUTHORIZED_KEY`: SSH public key injected by cloud-init

The example stores rendered files under
`.state/reproducible-environment/<name>/`:

- `user-data.yaml`: rendered cloud-init user-data
- `archie-instance-user-data.yaml`: rendered launch-time cloud-init user-data

## Guest Baseline

After successful bootstrap, the guest is expected to provide:

- Arch Linux from the configured cloud image
- functional network access through the default Incus network profile
- `git`
- Hyprland
- `openssh`
- SDDM installed and enabled
- a local password login for `${ARCHIE_VM_USERNAME}` at SDDM and the console
- one reboot after first-boot provisioning completes and before local graphical validation
- enough supporting packages to reach a graphical-ready baseline:
  `kitty`, `mesa`, `pipewire`, `seatd`, `sudo`, `waybar`,
  `xdg-desktop-portal-hyprland`

Cloud-init creates a bootstrap log bundle in `/var/log/archie-bootstrap/` with:

- cloud-init status
- journal excerpts for bootstrap-relevant units
- package presence checks
- network snapshot
- SSH enablement status
- SDDM enablement status

These logs are bootstrap evidence only. Once Archie deployment begins, later
failures should be treated separately.

## Graphical Interaction

The primary interaction mode in this phase is the local graphical console:

```bash
incus console --type=vga "${ARCHIE_IMAGE_INSTANCE_NAME}"
```

That opens the VM VGA console through Incus. Use it to:

- confirm the guest reaches the display manager
- log in locally for first validation
- inspect obvious graphical boot failures before trying guest-side Archie work

## Manual Archie Validation Loop

After the launched VM is up:

1. Create and start a VM from the published image.
2. Discover the guest IP and reconnect over SSH if needed.
3. Open the graphical console and confirm SDDM is reachable and accepts the
   configured local password.
4. Run `~/pull-archie-repo.sh` in the guest or mount a working tree into the instance.
5. Install any extra Archie dependencies that are still intentionally outside
   this bootstrap baseline.
6. Run the normal Archie deployment flow from the repository.
7. Reload or restart the affected service and iterate safely inside the VM.

This keeps provisioning failures distinct from Archie deployment failures:

- if cloud-init did not finish or the guest never reaches SDDM, debug bootstrap
- if bootstrap succeeded but Stow deployment fails, debug Archie deployment
- if deployment succeeds but Hyprland or other services misbehave, debug the
  Archie runtime separately

## Failure Boundaries

Use the following boundaries during debugging:

- host-side creation failure: image alias, Incus profile, storage, or VM limits
- cloud-init failure: package install, SSH setup, service enablement, or log capture
- guest baseline failure: networking, `git`, Hyprland, `openssh`, or SDDM missing after cloud-init completes
- Archie deployment failure: repo clone, package gaps beyond the baseline, Stow issues
- session/runtime failure: SDDM login, Hyprland session startup, Waybar, Dunst, or other Archie services

When the failure point is unclear, start with:

```bash
incus info "${ARCHIE_IMAGE_INSTANCE_NAME}"
ssh -i ~/.ssh/homelab archie@<guest-ip>
journalctl -u sshd -u sddm --no-pager
sudo ls -la /var/log/archie-bootstrap
incus console --type=vga "${ARCHIE_IMAGE_INSTANCE_NAME}"
```
