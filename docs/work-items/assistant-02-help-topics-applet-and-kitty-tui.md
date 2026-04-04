# Work Item 2: Design The Help Topics Applet And Kitty TUI Flow

<!--toc:start-->

- [Work Item 2: Design The Help Topics Applet And Kitty TUI Flow](#work-item-2-design-the-help-topics-applet-and-kitty-tui-flow)
  - [Status](#status)
  - [Outcome](#outcome)
  - [Decision changes](#decision-changes)
  - [Dependencies](#dependencies)
  - [Scope Notes](#scope-notes)
  - [Main quests](#main-quests)
  - [Exit Criteria](#exit-criteria)
<!--toc:end-->

Define the first Archie assistant interface as a lightweight GUI applet that
lists help topics and opens a Kitty terminal into a dedicated assistant TUI for
topic exploration.

## Status

Planned

## Outcome

Archie has a concrete interface and execution plan for an assistant that begins
with a graphical topic chooser and hands off into a terminal-native assistant
experience suitable for keyboard-first usage.

## Decision changes

- The assistant should begin as a GUI applet, not a full desktop shell.
- The GUI applet’s primary job is topic discovery and launch, while the deeper
  interaction happens inside a Kitty-hosted TUI.
- The TUI should be optimized for Archie’s keyboard-first workflow and should
  feel like a system help tool, not a generic chat shell.
- The first topic set should include keyboard shortcuts, important Zsh aliases
  and functions, and the architecture guide created by work item 1.
- The assistant should present documented information and curated helper flows
  before it attempts any agent-backed interaction.

## Dependencies

- [Work Item 1](assistant-01-system-architecture-guide.md) provides the
  architecture material needed for one of the assistant’s core topics.
- [`docs/user/KEYBOARD_SHORTCUTS.md`](../user/KEYBOARD_SHORTCUTS.md) provides
  an existing shortcut source the assistant should expose.
- Archie shell helper docs may need follow-up expansion if the current Zsh
  commands are not documented enough for assistant presentation.

## Scope Notes

Included:

- Define the applet interaction model and launch points.
- Define the topic taxonomy and how topics map to docs or generated views.
- Define how Kitty is launched and how the chosen topic is passed into the TUI.
- Define the TUI navigation and presentation contract.

Not included:

- Final implementation in a specific GUI or TUI toolkit.
- Background agent integration beyond the interface boundaries needed for later
  work.
- Broad in-app editing of the documentation corpus.

## Main quests

- Define the launch surface for the assistant applet, including where Archie
  users are expected to access it from.
- Define the initial topic menu, including at least:
  - keyboard shortcuts
  - important Zsh aliases and functions
  - system architecture
  - pointers to key operational documentation
- Decide how the GUI applet passes context into Kitty, such as:
  - selected topic identifier
  - requested mode
  - environment or config location for the TUI
- Define the TUI’s core interactions, including topic landing pages, search,
  back navigation, and command hints.
- Define how the assistant surfaces static docs versus generated summaries, and
  when it should open raw documentation directly.
- Identify documentation gaps discovered while shaping the topic set, including
  whether Archie needs a separate work item for shell-helper documentation.

## Exit Criteria

- Archie has a clear design for the assistant’s GUI-to-Kitty handoff.
- The initial topic map is explicit enough to implement without rediscovering
  the basic user experience.
- Any documentation gaps that block the assistant topic set are recorded as
  explicit follow-up work instead of being left implicit.
