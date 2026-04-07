# Design A Power And Peripherals Control GUI

Define the first Archie GUI as a focused control surface for power management
and peripherals whose behavior directly affects power usage.

## Status

Planned

## Outcome

Archie has a concrete, implementable design for a GUI that centralizes common
power-related controls such as screen state, backlight, and other attached
peripherals that draw power, without yet overcommitting to implementation
details that depend on the chosen desktop integration approach.

## Decision Changes

- This GUI is intended as the first work item under the `system-gui` epic.
- The GUI should optimize for real machine controls Archie already uses instead
  of becoming a generic desktop settings clone.
- The first design pass should treat screens, backlights, and comparable
  power-adjacent peripherals as one user-facing problem space when that keeps
  the interface coherent.
- The work should identify which controls are Archie-owned wrappers over system
  tools and which are direct integrations with tools such as `brightnessctl`,
  `hyprctl`, or related display-management commands.
- Notification, panel, or launcher integration can be considered, but should
  remain secondary to defining the main GUI contract.

## Scope Notes

Included:

- Define the user-facing tasks this GUI must support.
- Identify the hardware and software capabilities Archie can reliably detect
  and control.
- Define the likely information architecture for the GUI, including whether it
  is a single window, modal launcher flow, or another compact control surface.
- Define the command and script boundaries needed to support the GUI from this
  repository.

Not included:

- Final implementation in a specific GUI toolkit.
- Full battery analytics or long-term power profiling unless they are required
  for the core control workflow.
- Broad system-settings coverage unrelated to power or power-adjacent
  peripherals.

## Main Quests

- Define the primary user flows the GUI must handle, including at least:
  - display brightness changes
  - backlight changes for relevant devices
  - display enable, disable, or profile selection where Archie can support it
  - visibility into which connected peripherals are affecting power usage
- Inventory the current Archie tooling and system commands that already touch
  this problem space, and identify what is missing for a GUI-backed workflow.
- Decide what runtime data the GUI must read and how fresh that data needs to
  be for a responsive experience.
- Decide which actions should be immediate toggles or sliders and which should
  require confirmation because they can disrupt the current session.
- Define the minimum failure and fallback behavior for unsupported hardware,
  missing utilities, or partial permissions.
- Capture the implementation constraints that matter before coding starts,
  including:
  - candidate toolkit or stack choices
  - interaction with Hyprland and Wayland session tools
  - whether the GUI should be launched directly, from Rofi, or from another
    Archie entrypoint

## Acceptance Criteria

- Archie has a clear first-stage design for a power and peripherals GUI that
  can be implemented without reopening its basic scope.
- The planned GUI is grounded in Archie’s real command and device surface
  rather than abstract settings categories.
- The work item identifies the missing helper scripts or backend contracts that
  must exist before GUI implementation begins.

## Metadata

### id

system-gui-01
