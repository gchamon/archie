# Cloudinit

## Status

Done

## Outcome

Archie should have the cloud-init wrapper that provisions a base Arch cloud
image and executes the historical `archinstall` automation non-interactively.

## Decision Changes

- The VM-image pipeline should use official Arch Linux cloud images from
  `arch-boxes` as the base artifacts.
- Cloud-init should carry the unattended provisioning contract, parameter
  injection, and early log capture.
- The provisioning layer should make failures distinguishable between
  cloud-init behavior and installer logic.

## Dependencies

- [`vm-image-01-archinstall.md`](./vm-image-01-archinstall.md) completed
  outputs.

## Main Quests

- Use official Arch Linux cloud images from `arch-boxes` as base artifacts.
- Create `cloud-init` user-data and meta-data templates for unattended
  provisioning.
- Install and invoke the Python `archinstall` controller within the
  provisioning flow.
- Capture serial-console and cloud-init logs for troubleshooting.
- Define the parameterization strategy for installer-config injection.
- Document the local execution, debug workflow, and failure-handling
  expectations.

## Acceptance Criteria

- Provisioning boots from the official Arch cloud image and runs unattended.
- Cloud-init successfully triggers `archinstall` automation end-to-end.
- The resulting VM disk reaches installed Archie state and can boot.
- Logs clearly identify where failures occur between cloud-init and installer
  logic.

## Metadata

### id

vm-image-02
