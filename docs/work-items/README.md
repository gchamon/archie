# Work Items

<!--toc:start-->

- [Work Items](#work-items)
  - [Quest Subtypes](#quest-subtypes)
  - [Metadata](#metadata)
<!--toc:end-->

This directory contains staged plans for larger Archie changes that should be
implemented across multiple sessions.

For more information, see <https://docs.gitlab.com/user/work_items/>.

Work item filenames must follow the pattern
`{epic-name}-{work-item-number}-{work-item-name}.md`.

Each work item file should be self-contained enough to hand to an engineer or
agent for execution. The work item should define:

- the current planning status of the stage when useful
- the goal of the stage
- the expected outcome
- the main quests to complete
- any dependencies on earlier work items

Work items in this directory default to the GitLab work item type `Issue`
unless overridden in metadata.

Archie planning methodology uses this hierarchy:

- epics
- work items
- work item types: `Issue`, `OKR`, and `Test case`
- quests inside work items: main quests and side-quests

GitLab terminology mapping:

- work items correspond to GitLab work items:
  <https://docs.gitlab.com/user/work_items/>
- main quests and side-quests both correspond to GitLab tasks:
  <https://docs.gitlab.com/user/tasks/>
- `OKR` corresponds to GitLab OKRs:
  <https://docs.gitlab.com/user/okrs/>
- `Test case` corresponds to GitLab test cases:
  <https://docs.gitlab.com/ci/test_cases/>

Critical-chain rule:

- work items linked to epics with priority `critical` are part of the
  project's critical chain
- epic priority is defined canonically in [`docs/epics/README.md`](../epics/README.md)

## Quest Subtypes

Work items may group tasks by subtype when that makes the plan easier to
maintain.

- Main quests directly advance the stated outcome of the work item.
- Side-quests are bounded secondary tasks discovered while shaping or
  implementing the work item. They stay attached to the current work item when
  they materially affect the same docs, tooling, or helper flow and are too
  small to justify a separate work item.
- Side-quests should be labeled explicitly under `## Main quests`, either as their
  own subsection or as a clearly named grouping, so they do not get mixed into
  the main execution path by accident.

## Metadata

Work items may include a `## Metadata` subsection near the top when they need
to override default work item attributes.

- `type` defaults to `Issue` when omitted.
- Supported explicit `type` values are `Issue`, `OKR`, and `Test case`.
- `## Metadata` should treat metadata as nested Markdown structure.
- Each metadata key should be a `###` heading under `## Metadata`.
- The value should appear as the body content directly under that `###` key
  heading.

Example:

```md
## Metadata

### type

OKR
```

Naming rules:

- `epic-name`: lowercase kebab-case name shared by all work items in the same
  initiative.
- `work-item-number`: two-digit sequence number within the epic, such as `01`
  or `04`.
- `work-item-name`: lowercase kebab-case summary of the specific stage.

Example filenames:

- `deployment-management-01-design.md`
- `vm-image-03-qemu-image.md`

Status convention:

- work item files may include a `## Status` section near the top
- use short prose values such as `Planned`, `In progress`, `Reviewing` or `Complete`
- status communicates planning progress only and does not replace the work item
  body
- If the status is omitted, it's assumed to be `Backlog`

This directory also includes historical work item notes for past Archie work.

These files are planning artifacts. They describe the work; they are not the
implementation itself.
