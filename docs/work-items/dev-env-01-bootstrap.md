# Bootstrap The Archie Dev Env

Define and implement the base dev-env VM workflow for Archie development
using an Incus-managed Arch Linux virtual machine provisioned with cloud-init.

## Status

<!--
Use a short prose status for the current state of the work item.
Supported values are `backlog`, `planned`, `doing`, `done`, `cancelled`, and `abandoned`.
`killed` is reserved for GitLab graveyard history when a managed work item is removed from the repository.
-->

Done

## Outcome

Archie has a documented, repeatable way to create a reproducible Incus VM image
from a cloud-init-bootstrapped Arch guest, then launch disposable Archie test
instances from that image with a small launch-time cloud-init payload for
guest-side repo acquisition.

## Decision Changes

- This work replaces the old `vm-image` emphasis on unattended image artifacts
  with a dev-env emphasis.
- Incus VM is the canonical runtime for the first phase. Containers are out of
  scope for now.
- `cloud-init` remains in scope because it is the best bridge to later QEMU
  support without committing to QEMU-first implementation now.
- The first milestone is a graphical-ready Arch guest for manual Archie
  validation, not Archie deployment automation.
- Local graphical console access is the primary interaction mode for the guest.
- The guest baseline should be just enough to support Archie installation and
  debugging, not a full parity clone of the current host setup.
- The reproducible artifact for this phase is a stopped Incus VM published as a
  local Incus image alias, not a generic portable image pipeline.
- Launching a test VM from the published image may attach a second, minimal
  cloud-init payload for per-instance guest setup such as dropping a repo pull
  helper script into the Archie user home.

## Main Quests

- Define the reproducibility contract for the VM bootstrap flow, including:
  - base image source and versioning strategy
  - runtime inputs such as hostname, username, and resource sizing
  - generated metadata and log locations
  - which parts of the environment are expected to be reproducible in this
    phase versus manually iterated later
- Define the minimal guest baseline required after provisioning:
  - Arch Linux guest
  - networking functional
  - `git` available
  - Hyprland installed
  - SDDM installed and enabled as the display manager
  - enough supporting packages and services to start manual Archie testing
- Design the cloud-init shape for this phase, including package installation,
  service enablement, user setup, and log capture strategy.
- Define the repo-owned bootstrap entrypoints and inputs needed to create and
  reprovision the Incus VM without manual guest-side setup.
- Define the Incus VM lifecycle operations needed in this phase:
  - create
  - start
  - stop
  - rebuild
  - inspect
  - retrieve logs
- Document the local graphical interaction path for opening and using the
  guest's display during manual testing.
- Document the manual Archie validation loop that follows bootstrap:
  - enter the guest
  - clone or mount the Archie repo
  - manually install required packages as needed
  - manually run the Archie deployment flow
  - iterate on scripts or config safely inside the VM
- Define failure boundaries so provisioning issues can be distinguished from
  later Archie deployment or session startup issues.

## Acceptance Criteria

- A fresh Incus VM can be provisioned from a repo-documented workflow with no
  manual guest setup required before first login.
- The guest reaches a graphical-ready baseline with Hyprland and SDDM
  installed.
- `git` and networking are available in the guest.
- Logs and metadata are sufficient to diagnose bootstrap failures separately
  from later Archie issues.
- The environment is practical for repeated manual Archie testing and teardown.

## Metadata

### id

dev-env-01

## Implementation Notes

- Repo-owned cloud-init templates:
  `templates/dev-env/cloud-init/`
- User-facing workflow guide:
  `docs/development/DEV_ENV.md`
- Canonical runtime interface:
  direct `incus` CLI examples plus SSH into the guest
