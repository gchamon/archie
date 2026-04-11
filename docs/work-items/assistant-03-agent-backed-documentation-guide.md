# Add Agent-Backed Documentation Guidance To The Assistant

Define how the Archie assistant can optionally load a user-configured coding
agent and constrain it into a documentation and architecture guide role inside
the assistant experience.

## Status

<!--
Use a short prose status for the current state of the work item.
Supported values are `backlog`, `planned`, `doing`, `done`, `cancelled`, and `abandoned`.
`killed` is reserved for GitLab graveyard history when a managed work item is removed from the repository.
-->

Planned

## Outcome

Archie has an explicit plan for optional agent-backed assistance that can use
tools such as Codex, Claude, Gemini, or OpenCode as interactive guides without
making the assistant depend on any single provider.

## Decision Changes

- Agent support is optional and should layer on top of the documented
  assistant, not replace the non-agent topic browser.
- Archie should treat agent integration as a configuration problem with a
  stable local contract rather than hardcoding behavior around one provider.
- The loaded agent profile should constrain the agent toward documentation,
  architecture explanation, and safe guidance instead of broad repo mutation by
  default.
- Provider-specific setup should remain user-configured, but the assistant may
  supply prompt, context, and mode presets for supported agents.
- The assistant should degrade cleanly when no supported agent is configured.

## Dependencies

- [Work Item 1](assistant-01-system-architecture-guide.md) provides the
  architecture corpus the agent-assisted mode should prioritize.
- [Work Item 2](assistant-02-help-topics-applet-and-kitty-tui.md) defines the
  GUI and TUI surfaces where agent-backed guidance may appear.

## Scope Notes

Included:

- Define the supported integration model for external coding agents.
- Define how the assistant chooses, loads, and constrains an agent profile.
- Define the trust and safety boundaries for agent-backed guidance.
- Define the documentation and architecture context the assistant should inject
  into the agent session.

Not included:

- Supporting arbitrary autonomous code execution by the configured agent.
- Full multi-agent orchestration.
- Provider-specific deep integrations that exceed the shared assistant contract.

## Main Quests

- Define the local configuration model for supported agents, including:
  - provider identity
  - executable or invocation contract
  - prompt or instruction overlay
  - access to Archie documentation context
- Decide which agent capabilities are allowed inside assistant mode, such as:
  - documentation lookup
  - architecture explanation
  - command suggestion
  - read-only repository inspection
- Define the restrictions that keep assistant mode safe, including behavior
  when an agent wants to edit files, execute commands, or answer beyond the
  documented Archie scope.
- Define how the assistant should present provenance, confidence, and fallback
  behavior when the agent response goes beyond the local docs.
- Decide how Archie should package or generate agent-specific profiles for
  tools such as Codex, Claude, Gemini, and OpenCode without letting those
  profiles drift from the assistant’s canonical behavior contract.
- Define the minimum no-agent fallback behavior so the assistant remains useful
  even when no coding agent is configured.

## Acceptance Criteria

- Archie has an explicit agent-integration contract for assistant mode.
- The assistant can support multiple user-selected agents through a shared
  behavior model instead of per-provider ad hoc logic.
- Safety and fallback behavior are defined well enough that agent-backed mode
  does not undermine the documentation-first assistant experience.

## Metadata

### id

assistant-03
