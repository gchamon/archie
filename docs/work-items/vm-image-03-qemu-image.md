# QEMU Image

## Status

Done

## Outcome

Archie should have a repeatable historical pipeline that produces an executable
QCOW2 image for manual inspection in QEMU.

## Decision Changes

- The VM-image pipeline should combine the Arch cloud QCOW2 base image,
  cloud-init seed artifacts, and `archinstall` automation payload into one
  repeatable QEMU build flow.
- QEMU invocation should be standardized enough to keep the manual validation
  path consistent.
- Build outputs should preserve provenance through explicit manifests and
  troubleshooting notes.

## Dependencies

- [`vm-image-01-archinstall.md`](./vm-image-01-archinstall.md)
- [`vm-image-02-cloudinit.md`](./vm-image-02-cloudinit.md)

## Main Quests

- Automate image creation using the official Arch cloud QCOW2 base image,
  cloud-init seed artifacts, and `archinstall` automation payload.
- Standardize QEMU invocation, including UEFI, disk layout, CPU and memory
  defaults, and networking.
- Produce versioned output images and build metadata.
- Provide a one-command local run path for manual validation.
- Document troubleshooting notes for common boot and provisioning failures.

## Acceptance Criteria

- The pipeline builds an Archie QCOW2 image from scratch without interactive
  steps.
- The produced image boots in QEMU and reaches the expected desktop or login
  baseline.
- Build metadata makes image provenance reproducible.
- The manual inspection workflow is documented and executable.

## Metadata

### id

vm-image-03
