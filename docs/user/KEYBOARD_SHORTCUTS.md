# Keyboard shortcuts

<!--toc:start-->

- [Keyboard shortcuts](#keyboard-shortcuts)
  - [Window management](#window-management)
  - [Focus and workspaces](#focus-and-workspaces)
  - [Launchers and utilities](#launchers-and-utilities)
  - [Session and brightness](#session-and-brightness)
  - [Mouse actions](#mouse-actions)

<!--toc:end-->

The bindings are defined in `deployment-packages/config/hypr/config/binds.lua`.

## Window management

| Shortcut | Description |
| :-- | :-- |
| `SUPER + Q` | Launches Kitty. |
| `SUPER + C` | Closes the active window. |
| `SUPER + E` | Launches the Kitty Ranger file manager. |
| `SUPER + W` | Opens the Rofi window menu. |
| `SUPER + J` / `SUPER + SHIFT + J` | Toggles or swaps the dwindle split direction. |
| `SUPER + SHIFT + F` / `SUPER + F` | Toggles floating or fullscreen mode. |
| `SUPER + SHIFT + Arrow` | Swaps the active window in that direction. |
| `SUPER + CTRL + SHIFT + Arrow` | Moves the active window in that direction. |

## Focus and workspaces

| Shortcut | Description |
| :-- | :-- |
| `SUPER + Arrow` | Moves focus in that direction. |
| `SUPER + SHIFT + Mouse Up/Down` | Moves focus left/right. |
| `SUPER + [1-9, 0]` | Switches to workspace 1–10. |
| `CTRL + ALT + Right/Left` | Switches to the next/previous monitor workspace. |
| `CTRL + ALT + equal` | Switches to the next relative workspace. |
| `SUPER + SHIFT + [1-9, 0]` | Moves the active window to workspace 1–10. |
| `SUPER + SHIFT + L/H` | Moves the active window to the next/previous relative workspace. |
| `SUPER + TAB` | Switches to the previous workspace. |
| `SUPER + CTRL + Right/Left` | Moves the active window to monitor 1/0. |
| `SUPER + Mouse Down/Up` | Switches to the next/previous existing workspace. |
| `SUPER + S` / `SUPER + SHIFT + S` | Toggles the `magic` special workspace or moves the active window there. |

## Launchers and utilities

| Shortcut | Description |
| :-- | :-- |
| `SUPER + R` | Opens the Rofi application launcher. |
| `SUPER + SHIFT + R` | Opens the Archie shell menu. |
| `SUPER + CTRL + SHIFT + R` | Opens the Rofi terminal-history menu. |
| `SUPER + V` | Opens the cliphist menu. |
| `SHIFT + Print` / `Print` | Captures the full screen or a selected area. |
| `CTRL + Escape` | Launches GNOME System Monitor. |

## Session and brightness

| Shortcut | Description |
| :-- | :-- |
| `SUPER + M` | Prompts before exiting Hyprland. |
| `SUPER + SHIFT + M` / `SUPER + CTRL + M` | Prompts before powering off or rebooting. |
| `XF86PowerOff` | Prompts before powering off. |
| `SUPER + CTRL + ALT + R` | Reloads the Hyprland configuration. |
| `SUPER + CTRL + S` | Toggles display DPMS. |
| `SUPER + L` | Locks with Hyprlock. |
| `Lid Switch close/open` | Applies the configured lid-close policy. |
| `SUPER + CTRL + KP_Add/KP_Subtract` | Increases/decreases brightness by 10%. |
| `XF86MonBrightnessUp/Down` | Increases/decreases brightness by 10%. |

## Mouse actions

| Shortcut | Description |
| :-- | :-- |
| `SUPER + LMB` (`mouse:272`) | Moves the active window while dragging. |
| `SUPER + RMB` (`mouse:273`) | Resizes the active window while dragging. |
