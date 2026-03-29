# Dev Environment

<!--toc:start-->

- [Dev Environment](#dev-environment)
  - [Scope](#scope)
  - [Prerequisites](#prerequisites)
  - [Creating a reproducible image](#creating-a-reproducible-image)
    - [1. Optionally export overrides](#1-optionally-export-overrides)
    - [2. Create and publish the base image](#2-create-and-publish-the-base-image)
  - [Launching an Archie instance from the reproducible image](#launching-an-archie-instance-from-the-reproducible-image)
    - [1. Optionally export overrides](#1-optionally-export-overrides-1)
    - [2. Launch the Archie instance](#2-launch-the-archie-instance)
    - [3. Launch the graphical console](#3-launch-the-graphical-console)
    - [4. Start bidirectional clipboard sync](#4-start-bidirectional-clipboard-sync)
  - [Cleanup](#cleanup)
  - [Runtime Inputs](#runtime-inputs)
  - [Guest Baseline](#guest-baseline)
  - [Graphical Interaction](#graphical-interaction)
  - [Manual Archie Validation Loop](#manual-archie-validation-loop)
  - [Failure Boundaries](#failure-boundaries)
<!--toc:end-->

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
[docs/user/DEVELOPMENT.md](../user/DEVELOPMENT.md#incus-install).

The bootstrap workflow expects:

- `incus`
- `envsubst`
- `jq`
- `ssh`
- `wl-copy`
- `wl-paste`

## Creating a reproducible image

The canonical interface is the Incus CLI plus the repo-owned templates. The
helper scripts under `scripts/` are convenience wrappers around this documented
flow.

### 1. Optionally export overrides

```bash
export ARCHIE_BASE_VM_NAME="archie-dev"
export ARCHIE_BASE_VM_HOSTNAME="archie-dev"
export ARCHIE_BASE_VM_USERNAME="archie"
export ARCHIE_BASE_SOURCE_IMAGE="images:archlinux/current/cloud"
export ARCHIE_BASE_IMAGE_ALIAS="archie/reproducible-baseline"
export ARCHIE_BASE_VM_CPU_LIMIT="4"
export ARCHIE_BASE_VM_MEMORY="8GiB"
export ARCHIE_BASE_VM_ROOT_DISK_SIZE="32GiB"
export ARCHIE_BASE_VM_PASSWORD_HASH="$(openssl passwd -6 'archie')"
export ARCHIE_BASE_VM_SSH_AUTHORIZED_KEY="$(< ~/.ssh/homelab.pub)"
```

If you do not export them first, the documented flow falls back to these
defaults:

- `ARCHIE_BASE_VM_NAME=archie-dev`
- `ARCHIE_BASE_VM_HOSTNAME=archie-dev`
- `ARCHIE_BASE_VM_USERNAME=archie`
- `ARCHIE_BASE_SOURCE_IMAGE=images:archlinux/current/cloud`
- `ARCHIE_BASE_IMAGE_ALIAS=archie/reproducible-baseline`
- `ARCHIE_BASE_VM_CPU_LIMIT=4`
- `ARCHIE_BASE_VM_MEMORY=8GiB`
- `ARCHIE_BASE_VM_ROOT_DISK_SIZE=32GiB`
- `ARCHIE_BASE_VM_SSH_AUTHORIZED_KEY` from `~/.ssh/homelab.pub`
- `ARCHIE_BASE_VM_PASSWORD_HASH` from `openssl passwd -6 'archie'`

### 2. Create and publish the base image

```bash
base_state_dir=".state/dev-env/${ARCHIE_BASE_VM_NAME}"
mkdir -p "${base_state_dir}"

envsubst < templates/dev-env/cloud-init/user-data.yaml.tpl \
  > "${base_state_dir}/user-data.yaml"

incus init "${ARCHIE_BASE_SOURCE_IMAGE}" "${ARCHIE_BASE_VM_NAME}" --vm \
  --config limits.cpu="${ARCHIE_BASE_VM_CPU_LIMIT}" \
  --config limits.memory="${ARCHIE_BASE_VM_MEMORY}"

incus config set "${ARCHIE_BASE_VM_NAME}" cloud-init.user-data - \
  < "${base_state_dir}/user-data.yaml"
incus config device override "${ARCHIE_BASE_VM_NAME}" root \
  size="${ARCHIE_BASE_VM_ROOT_DISK_SIZE}"

incus start "${ARCHIE_BASE_VM_NAME}"
```

Wait for the Incus agent first. Early in boot, `incus exec` can still fail with
`Error: VM agent isn't currently running`, so treat that as a retry condition
until the agent becomes available.

Then wait for cloud-init to finish:

```bash
incus exec "${ARCHIE_BASE_VM_NAME}" -- cloud-init status --wait
```

Stop the VM and publish it into the local Incus image store:

```bash
incus stop "${ARCHIE_BASE_VM_NAME}"

incus publish "${ARCHIE_BASE_VM_NAME}" \
  --alias "${ARCHIE_BASE_IMAGE_ALIAS}" \
  --reuse \
  "archie.base_image=${ARCHIE_BASE_SOURCE_IMAGE}"
```

That renders the bootstrap cloud-init under
`.state/dev-env/${ARCHIE_BASE_VM_NAME}/`, creates the VM, waits for cloud-init,
stops the VM, and publishes the image alias with `--reuse`.

If you prefer the convenience wrapper, `./scripts/create-arch-base-image.sh`
implements the same flow and defaults.

## Launching an Archie instance from the reproducible image

### 1. Optionally export overrides

```bash
export ARCHIE_INSTANCE_IMAGE_ALIAS="archie/reproducible-baseline"
export ARCHIE_INSTANCE_NAME="archie-dev-from-image"
export ARCHIE_INSTANCE_USERNAME="archie"
export ARCHIE_INSTANCE_REPO_URL="https://gitlab.com/gabriel.chamon/archie.git"
export ARCHIE_INSTANCE_SSH_IDENTITY="${HOME}/.ssh/homelab"
export ARCHIE_INSTANCE_MEMORY="4GiB"
```

`ARCHIE_INSTANCE_USERNAME` must match the user already present in the published
image. In the current flow that is the same account created during the
bootstrap phase.

If you do not export them first, the documented flow falls back to these
defaults:

- `ARCHIE_INSTANCE_IMAGE_ALIAS=archie/reproducible-baseline`
- `ARCHIE_INSTANCE_NAME=archie-dev-from-image`
- `ARCHIE_INSTANCE_USERNAME=archie`
- `ARCHIE_INSTANCE_REPO_URL=https://gitlab.com/gabriel.chamon/archie.git`
- `ARCHIE_INSTANCE_SSH_IDENTITY=${HOME}/.ssh/homelab`
- `ARCHIE_INSTANCE_MEMORY=4GiB`

### 2. Launch the Archie instance

```bash
instance_state_dir=".state/dev-env/${ARCHIE_INSTANCE_NAME}"
mkdir -p "${instance_state_dir}"

envsubst < templates/dev-env/cloud-init/archie-instance-user-data.yaml.tpl \
  > "${instance_state_dir}/archie-instance-user-data.yaml"

cp templates/dev-env/incus/archie-instance-raw-qemu.conf \
  "${instance_state_dir}/archie-instance-raw-qemu.conf"

incus init "${ARCHIE_INSTANCE_IMAGE_ALIAS}" "${ARCHIE_INSTANCE_NAME}" --vm \
  --config limits.memory="${ARCHIE_INSTANCE_MEMORY}"

incus config set "${ARCHIE_INSTANCE_NAME}" raw.qemu.conf - \
  < "${instance_state_dir}/archie-instance-raw-qemu.conf"
incus config set "${ARCHIE_INSTANCE_NAME}" cloud-init.user-data - \
  < "${instance_state_dir}/archie-instance-user-data.yaml"

incus start "${ARCHIE_INSTANCE_NAME}"
```

Wait for the Incus agent first, then wait for cloud-init:

```bash
incus exec "${ARCHIE_INSTANCE_NAME}" -- cloud-init status --wait
```

Discover the guest IP:

```bash
guest_ip="$(
  incus list "${ARCHIE_INSTANCE_NAME}" --format json \
    | jq -r --arg vm_name "${ARCHIE_INSTANCE_NAME}" '
        .[]
        | select(.name == $vm_name)
        | .state.network
        | to_entries[]
        | select(.key != "lo")
        | .value.addresses[]?
        | select(.family == "inet" and .scope != "link")
        | .address
      ' \
    | head -n 1
)"
printf 'Guest IP: %s\n' "${guest_ip}"
```

That renders launch-time cloud-init under
`.state/dev-env/${ARCHIE_INSTANCE_NAME}/`, copies the `virtio-vga` override,
creates the VM from the published image, waits for cloud-init, and prints the
guest IP.

Like the bootstrap flow, wait for the Incus VM agent to become available before
you rely on `incus exec` or start `cloud-init status --wait`.

That launch-time cloud-init writes `~/pull-archie-repo.sh` for
`${ARCHIE_INSTANCE_USERNAME}` so the Archie repo can be cloned or updated on
demand inside the instance, and ensures `wl-clipboard` is available in the
guest for clipboard bridging.

If you prefer the convenience wrapper, `./scripts/launch-archie-instance.sh`
implements the same flow and defaults.

### 3. Launch the graphical console

```bash
incus console --type=vga "${ARCHIE_INSTANCE_NAME}"
```

If you prefer the convenience wrapper, `./scripts/launch-console.sh`
implements the same command.

For an interactive SSH shell instead of the VGA console, use:

```bash
ssh -i "${ARCHIE_INSTANCE_SSH_IDENTITY}" "${ARCHIE_INSTANCE_USERNAME}@${guest_ip}"
```

If you prefer the convenience wrapper, `./scripts/open-shell.sh` resolves the
guest IP and runs the same SSH command.

### 4. Start bidirectional clipboard sync

```bash
scripts/dev-env/ssh-clipboard-sync.sh \
  --identity "${ARCHIE_INSTANCE_SSH_IDENTITY}" \
  "${ARCHIE_INSTANCE_USERNAME}@${guest_ip}"
```

This keeps the graphical console and Hyprland session separate from clipboard
transport and avoids relying on native SPICE clipboard behavior inside Wayland.
The bridge is intended for text clipboard sync and auto-detects the active
Wayland socket on both sides when `WAYLAND_DISPLAY` is unset. It defaults to
`ARCHIE_INSTANCE_SSH_IDENTITY="${HOME}/.ssh/homelab"` if that variable is not
already exported.

If you prefer the convenience wrapper, `./scripts/setup-shared-clipboard.sh`
resolves the guest IP and runs the same clipboard bridge.

## Cleanup

To remove the launched Archie instance and its rendered launch-state files
without touching the base image alias:

```bash
if incus info "${ARCHIE_INSTANCE_NAME}" >/dev/null 2>&1; then
  if [[ "$(incus info "${ARCHIE_INSTANCE_NAME}" | awk '/^Status:/ { print $2 }')" == "RUNNING" ]]; then
    incus stop "${ARCHIE_INSTANCE_NAME}"
  fi

  incus delete "${ARCHIE_INSTANCE_NAME}"
fi

rm -rf ".state/dev-env/${ARCHIE_INSTANCE_NAME}"
```

This is the supported cleanup path for disposable test guests. Base image and
bootstrap VM cleanup remain manual so they can be handled intentionally.

If you prefer the convenience wrapper, `./scripts/cleanup-archie-instance.sh`
implements the same cleanup.

## Runtime Inputs

The documented flow standardizes these runtime inputs:

- `ARCHIE_BASE_VM_NAME`: bootstrap VM instance name and bootstrap state directory key
- `ARCHIE_BASE_VM_HOSTNAME`: bootstrap guest hostname
- `ARCHIE_BASE_VM_USERNAME`: bootstrap guest user
- `ARCHIE_BASE_VM_PASSWORD_HASH`: SHA-512 password hash for bootstrap local login
- `ARCHIE_BASE_VM_SSH_AUTHORIZED_KEY`: SSH public key injected into the bootstrap VM
- `ARCHIE_BASE_IMAGE_ALIAS`: published Incus image alias produced from the bootstrap VM
- `ARCHIE_INSTANCE_IMAGE_ALIAS`: published Incus image alias used to launch Archie test VMs
- `ARCHIE_INSTANCE_NAME`: launched Archie VM name
- `ARCHIE_INSTANCE_USERNAME`: guest user used for Archie test work inside the launched VM; this must match the account already present in the published image
- `ARCHIE_INSTANCE_REPO_URL`: Archie repository URL used by `~/pull-archie-repo.sh`
- `ARCHIE_INSTANCE_SSH_IDENTITY`: SSH private key path used by the shared
  clipboard helper, defaulting to `~/.ssh/homelab`

The scripts store rendered files under separate phase-specific state
directories:

- `${base_state_dir}/user-data.yaml`: rendered bootstrap cloud-init user-data
- `${instance_state_dir}/archie-instance-user-data.yaml`: rendered launch-time cloud-init user-data
- `${instance_state_dir}/archie-instance-raw-qemu.conf`: launched-instance QEMU override for the graphical console

## Guest Baseline

After successful bootstrap, the guest is expected to provide:

- Arch Linux from the configured cloud image
- functional network access through the default Incus network profile
- `git`
- Hyprland
- `openssh`
- SDDM installed and enabled
- `wl-clipboard`
- a local password login for `${ARCHIE_BASE_VM_USERNAME}` at SDDM and the console
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
incus console --type=vga "${ARCHIE_INSTANCE_NAME}"
```

That opens the VM VGA console through Incus. Use it to:

- confirm the guest reaches the display manager
- log in locally for first validation
- verify the `virtio-vga` launch override provides an acceptably smooth console experience
- inspect obvious graphical boot failures before trying guest-side Archie work

Clipboard sharing inside Hyprland is supported through the SSH clipboard bridge
instead of the SPICE console itself.

## Manual Archie Validation Loop

After the launched VM is up:

1. Create and start a VM from the published image.
2. Discover the guest IP and reconnect over SSH if needed.
3. Start `scripts/dev-env/ssh-clipboard-sync.sh` from the host.
4. Open the graphical console and confirm SDDM is reachable and accepts the
   configured local password.
5. Verify host-to-guest and guest-to-host text clipboard flow inside Hyprland.
6. Run `~/pull-archie-repo.sh` in the guest or mount a working tree into the instance.
7. Install any extra Archie dependencies that are still intentionally outside
   this bootstrap baseline.
8. Run the normal Archie deployment flow from the repository.
9. Reload or restart the affected service and iterate safely inside the VM.

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
incus info "${ARCHIE_INSTANCE_NAME}"
ssh -i ~/.ssh/homelab archie@<guest-ip>
journalctl -u sshd -u sddm --no-pager
sudo ls -la /var/log/archie-bootstrap
incus console --type=vga "${ARCHIE_INSTANCE_NAME}"
wl-paste
```
