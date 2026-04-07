# Epics

Epics group related work items when the scope is larger than a single
execution pass.

Use an epic when you need to coordinate:

- multiple work items against one outcome
- staged extraction from source material
- cross-cutting methodology changes

Epics should summarize intent and point to the active work items rather than
repeat their full detail.

## Standard Shape

Each epic should use:

- `Status`
- `Outcome`
- `Decision Changes`
- `Main Quests`
- `Acceptance Criteria`
- `Metadata`

## Metadata

Epics may include a `## Metadata` section when they need to override planning
defaults.

- `id` is required and must remain stable across renames and moves
- `child_ids` is required and should list the stable IDs of tracked work items
- `priority` defaults to `normal`
- supported explicit values are `critical`, `high`, and `normal`
- each metadata key should be a `###` heading under `## Metadata`

GitLab sync treats `child_ids` as the source of truth for epic membership.
When Archie runs in a personal namespace, epic proxy issues should link their
child work items through managed `relates_to` issue links.

Example:

```md
## Metadata

### id

deployment-management

### child_ids

- deployment-management-01
- deployment-management-02

### priority

critical
```

## Status Convention

Epics should use short prose values such as:

- `Planned`
- `Doing`
- `Done`

## Migration

Older Archie planning documents that predate stable IDs should add a stable
`id` to each epic and a `child_ids` list for the tracked work items that epic
owns. Keep those IDs stable even if files are renamed or moved.

## Critical Chain

Work items linked to epics with priority `critical` are on the project's
critical chain by default. Epics with priority `high` are important, but do
not automatically place every linked work item on the critical chain.

## Current Epics

### `deployment-management`

- Definition: [deployment-management.md](./deployment-management.md)
- Scope: Deployment and maintenance of Archie configuration across home, XDG,
  and system-managed paths.

### `vm-image`

- Definition: [vm-image.md](./vm-image.md)
- Scope: Historical VM image pipeline work around `archinstall`, cloud-init,
  QEMU image creation, and automated validation.

### `dev-env`

- Definition: [dev-env.md](./dev-env.md)
- Scope: Repeatable Archie development VM workflow around an Incus-managed Arch
  guest.

### `system-gui`

- Definition: [system-gui.md](./system-gui.md)
- Scope: First-party graphical interfaces for Archie system operations.

### `homepage`

- Definition: [homepage.md](./homepage.md)
- Scope: Archie’s public-facing homepage, product positioning, and supporting
  proof points.

### `assistant`

- Definition: [assistant.md](./assistant.md)
- Scope: An Archie assistant experience spanning GUI, TUI, and optional coding
  agent integration.

### `immutability`

- Definition: [immutability.md](./immutability.md)
- Scope: Evaluation of immutable or image-style system management for Archie,
  starting with an `arkdep` proof of concept in an isolated VM.
