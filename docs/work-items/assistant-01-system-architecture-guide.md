# Create A System Architecture Guide For The Assistant

Create the architecture documentation baseline the assistant will need before
it can reliably guide users through how Archie is structured and operated.

## Status

Planned

## Outcome

Archie has a user-comprehensible system architecture guide that explains the
major components, ownership boundaries, and operational flows of the current
system in a form that both humans and assistant tooling can consume.

## Decision Changes

- Existing architecture material is not yet sufficient for the assistant on
  its own. The current docs are useful, but they are fragmented across distro
  planning notes, ADRs, user guides, and repo structure descriptions.
- The assistant should rely on an explicit architecture guide instead of
  inferring Archie’s system model from scattered docs at runtime.
- The architecture guide should describe the current Archie system as it exists
  today, not only future distro ambitions or isolated design decisions.
- This work item exists to support the `assistant` epic directly and should be
  treated as a foundational dependency for assistant topics about system
  architecture.

## Scope Notes

Included:

- Define the major Archie subsystems and how they relate.
- Explain which directories and deployment packages own which parts of the
  system.
- Document the runtime relationships between Hyprland, Waybar, shell setup,
  Neovim, deployment tooling, and backup tooling where relevant.
- Provide a navigation-friendly structure suitable for terminal and assistant
  presentation.

Not included:

- Replanning the Archie architecture itself.
- Exhaustive per-file documentation for every repo path.
- Distro-ISO planning beyond the amount needed to distinguish it from the
  current Archie deployment model.

## Main Quests

- Define the intended audience and reading modes for the architecture guide,
  including:
  - direct human reading in Markdown
  - terminal or TUI topic browsing
  - agent-assisted question answering
- Create or designate a canonical architecture document that explains at least:
  - Archie’s deployment model
  - config ownership by major directory and Stow package
  - runtime desktop components and how they are launched
  - machine-specific configuration boundaries
  - documentation categories and where to find operational guidance
- Identify the existing docs that should be linked, summarized, or normalized
  instead of duplicated.
- Define the minimum terminology the assistant may assume when presenting
  system concepts, so topic names stay stable across GUI, TUI, and agent modes.
- Record known blind spots where architecture documentation is still thin and
  should remain out of scope until later work justifies expanding it.

## Acceptance Criteria

- Archie has a clear architecture guide suitable for use by the assistant.
- The guide is explicit enough that assistant topics do not have to guess how
  the system is organized.
- The work item links the guide cleanly to existing user, development, and ADR
  documentation instead of creating disconnected duplicate docs.

## Metadata

### id

assistant-01
