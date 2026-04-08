# Assistant

## Status

Planned

## Outcome

Archie should gain an assistant experience that starts with a lightweight GUI
topic picker, hands off into a Kitty-hosted TUI for deeper guidance, and can
optionally layer in constrained coding-agent support without replacing the
documentation-first workflow.


## Work items

- [assistant-01-system-architecture-guide](/docs/work-items/assistant-01-system-architecture-guide.md)
- [assistant-02-help-topics-applet-and-kitty-tui](/docs/work-items/assistant-02-help-topics-applet-and-kitty-tui.md)
- [assistant-03-agent-backed-documentation-guide](/docs/work-items/assistant-03-agent-backed-documentation-guide.md)

## Decision Changes

- The assistant should begin as a documentation and guidance surface, not as a
  broad automation shell.
- The first user journey should start from a lightweight GUI topic picker and
  continue inside a terminal-native interface that fits Archie’s
  keyboard-first workflow.
- Optional coding-agent integrations should remain constrained by Archie’s
  local documentation and architecture material instead of defining the
  assistant experience on their own.

## Main Quests

- Establish the architecture guide the assistant needs as a reliable local
  knowledge base.
- Define the GUI-to-Kitty handoff, topic taxonomy, and TUI behavior contract.
- Define the optional agent-backed mode so it remains documentation-first and
  provider-agnostic.

## Acceptance Criteria

- Contributors can identify the staged assistant plan without reading every
  child work item in full.
- The epic records the intended documentation-first boundary for assistant
  behavior.
- The epic exposes a stable `id` and explicit `child_ids` for synchronization.

## Metadata

### id

assistant

### child_ids

- assistant-01
- assistant-02
- assistant-03
