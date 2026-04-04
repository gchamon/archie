# `assistant`

This epic covers an Archie assistant experience that starts as a lightweight
GUI applet listing help topics, then hands off into a Kitty-hosted TUI for
interactive guidance about the system. The assistant should help users explore
keyboard shortcuts, important shell helpers, and Archie architecture and
documentation without forcing them to search the repository manually.

The epic also covers optional integration with user-configured coding agents
such as Codex, Claude, Gemini, or OpenCode, where Archie can load a constrained
assistant-oriented configuration so those agents behave like interactive guides
for the documented system.

## Work items

- [assistant-01-system-architecture-guide](../work-items/assistant-01-system-architecture-guide.md)
- [assistant-02-help-topics-applet-and-kitty-tui](../work-items/assistant-02-help-topics-applet-and-kitty-tui.md)
- [assistant-03-agent-backed-documentation-guide](../work-items/assistant-03-agent-backed-documentation-guide.md)
