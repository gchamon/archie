# Work Items

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
- the key tasks to complete
- any dependencies on earlier work items

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
