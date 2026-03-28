# Documentation Workspace

This directory holds Archie documentation and repo-internal working material.

- `agents/`: task briefs intended to be read and executed by coding agents.
- `epics/`: high-level initiative definitions aligned with GitLab epics as a work item type.
- `work-items/`: staged implementation plans and work item notes for larger changes.
  These are repo-local planning artifacts aligned with GitLab work items, not GitLab milestones.
- `architecture/`: architecture and distro design notes.
  Architecture decisions are recorded under `architecture/decisions/`.
- `assets/`: images used by the documentation.

The remaining Markdown files in this directory are the user-facing guides for
installing, operating, and maintaining Archie.

Relevant operational guides include:

- `GUIDE.md`: main Archie installation and deployment handbook.
- `DEVELOPMENT.md`: host-side development tooling and virtualization setup.
- `REPRODUCIBLE_ENVIRONMENT.md`: Incus VM bootstrap flow for disposable Archie
  development guests.
