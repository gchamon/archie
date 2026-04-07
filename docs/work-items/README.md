# Work Items

Work items define executable changes and preserve the reasoning needed to make
those changes durable.

## Standard Shape

Each work item should use:

- `Status`
- `Outcome`
- `Decision Changes`
- `Main Quests`
- `Acceptance Criteria`

Additional sections such as `Dependencies`, `Scope Notes`, `Manual Testing`,
or `Implementation Notes` may appear when they materially help execution, but
the standard shape above should remain present.

## Naming

Work item filenames should follow:

`{epic-name}-{work-item-number}-{work-item-name}.md`

Use lowercase kebab-case for the epic and work item names. Use a zero-padded
sequence such as `01` for the work item number.

Example:

- `deployment-management-01-design.md`

## Metadata

Work items may include a `## Metadata` section when they need to override
defaults or preserve important planning attributes.

- `id` is required for tracked work items and must remain stable across renames
  and moves
- `type` defaults to `Issue` when omitted
- supported explicit values are `Issue`, `OKR`, and `Test case`
- each metadata key should be a `###` heading under `## Metadata`

Example:

```md
## Metadata

### id

deployment-management-01

### type

OKR
```

## Style

The work item should tell a story. Each section should introduce the reader to
the concepts required and use technical prose to instruct the implementer. The
only exception is in tasks, which may be simple lists or subsections when the
task structure needs more detail.

## Quest Subtypes

Work items may group tasks by subtype when that makes the plan easier to
maintain.

- Main quests directly advance the stated outcome of the work item.
- Side-quests are bounded secondary tasks discovered while shaping or
  implementing the work item. They stay attached to the current work item when
  they materially affect the same docs, tooling, or helper flow and are too
  small to justify a separate work item.
- Side-quests should be labeled explicitly under `## Main Quests`, either as
  their own subsection or as a clearly named grouping, so they do not get
  mixed into the main execution path by accident.

## GitLab Mapping

Archie keeps GitLab-first planning vocabulary as the default methodology
language:

- work items correspond to GitLab work items
- main quests and side-quests correspond to GitLab tasks
- `OKR` corresponds to GitLab OKRs
- `Test case` corresponds to GitLab test cases

## Status Convention

If a work item includes `## Status`, use short prose values such as:

- `Backlog`
- `Planned`
- `Doing`
- `Done`

If status is omitted, treat the work item as `Backlog`.

## Migration

Older Archie planning documents that predate stable IDs should add a stable
`id` to each tracked work item. Keep the ID stable even if the file is
renamed or moved.

## Critical Chain

Work items linked to epics with priority `critical` are part of the project's
critical chain. Epic priority is defined canonically in
[`docs/epics/README.md`](../epics/README.md).

These files are planning artifacts. They describe the work; they are not the
implementation itself.
