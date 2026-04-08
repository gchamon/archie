# VM Image

## Status

Done

## Outcome

Archie should retain a historical planning record for the unattended VM image
pipeline that covered `archinstall` automation, cloud-init provisioning, QEMU
image creation, and automated validation, even though new VM-focused work now
centers on the `dev-env` epic instead.


## Work items

- [vm-image-01-archinstall](/docs/work-items/vm-image-01-archinstall.md)
- [vm-image-02-cloudinit](/docs/work-items/vm-image-02-cloudinit.md)
- [vm-image-03-qemu-image](/docs/work-items/vm-image-03-qemu-image.md)
- [vm-image-04-test-pipeline](/docs/work-items/vm-image-04-test-pipeline.md)

## Decision Changes

- The `vm-image` epic remains useful as historical planning context even though
  it is no longer the active direction for new development.
- The work should stay grouped as one completed pipeline narrative covering
  installer automation, provisioning, image creation, and validation.
- New VM workflow investment should prefer the `dev-env` initiative.

## Main Quests

- Preserve the historical planning sequence for unattended VM image work.
- Make the handoff from this archived direction to `dev-env` explicit.

## Acceptance Criteria

- Readers can understand that this epic is historical context rather than the
  current active path.
- The epic exposes a stable `id` and explicit `child_ids`.
- The epic records the relationship between the completed VM-image track and
  the active `dev-env` direction.

## Metadata

### id

vm-image

### child_ids

- vm-image-01
- vm-image-02
- vm-image-03
- vm-image-04
