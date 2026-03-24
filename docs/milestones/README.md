# Milestones

This directory contains staged plans for larger Archie changes that should be
implemented across multiple sessions.

Milestone filenames must follow the pattern
`{epic-name}-{milestone-number}-{milestone-name}.md`.

Each milestone file should be self-contained enough to hand to an engineer or
agent for execution. The milestone should define:

- the current planning status of the stage when useful
- the goal of the stage
- the expected outcome
- the key tasks to complete
- any dependencies on earlier milestones

Naming rules:

- `epic-name`: lowercase kebab-case name shared by all milestones in the same
  initiative.
- `milestone-number`: two-digit sequence number within the epic, such as `01`
  or `04`.
- `milestone-name`: lowercase kebab-case summary of the specific stage.

Example filenames:

- `deployment-management-01-design.md`
- `vm-image-03-qemu-image.md`

Status convention:

- milestone files may include a `## Status` section near the top
- use short prose values such as `Planned` or `Complete`
- status communicates planning progress only and does not replace the milestone
  body

This directory also includes historical milestone notes for past Archie work.

These files are planning artifacts. They describe the work; they are not the
implementation itself.
