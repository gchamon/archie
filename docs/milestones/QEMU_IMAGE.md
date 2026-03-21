# Milestone: QEMU Image

## Goal
Build a repeatable pipeline that produces an executable Archie QCOW2 image for manual inspection.

## Scope
- Automate image creation using:
  - official Arch cloud QCOW2 base image,
  - cloud-init seed artifacts,
  - archinstall automation payload.
- Standardize QEMU invocation (UEFI, disk layout, CPU/memory defaults, networking).
- Produce versioned output images and build metadata.
- Provide a one-command local run path for manual validation.

## Out of Scope
- Full CI test gating.
- Multi-hypervisor support.
- Release-grade distribution of images.

## Inputs
- Cloud-init artifacts from `CLOUDINIT` milestone.
- Archinstall automation from `ARCHINSTALL` milestone.

## Deliverables
- Build script/pipeline that outputs Archie QCOW2 images.
- Runtime script to boot produced image in QEMU for manual inspection.
- Build manifest containing source commit, base image version, and parameters used.
- Troubleshooting notes for common boot/provisioning failures.

## Acceptance Criteria
- Pipeline builds an Archie QCOW2 image from scratch without interactive steps.
- Produced image boots in QEMU and reaches expected desktop/login baseline.
- Build metadata makes image provenance reproducible.
- Manual inspection workflow is documented and executable.

## Dependencies
- `docs/milestones/ARCHINSTALL.md` and `docs/milestones/CLOUDINIT.md`.

