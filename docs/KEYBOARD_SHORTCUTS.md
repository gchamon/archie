# Keyboard shortcuts

<!--toc:start-->
- [Keyboard shortcuts](#keyboard-shortcuts)
  - [Window Management](#window-management)
  - [Focus and Workspace Navigation](#focus-and-workspace-navigation)
  - [Application Launchers and Utilities](#application-launchers-and-utilities)
  - [Session Management](#session-management)
  - [Brightness Control](#brightness-control)
  - [Window Resizing and Movement (Mouse)](#window-resizing-and-movement-mouse)
<!--toc:end-->

## Window Management

| Shortcut                     | Command/Action        | Description                                  |
| :--------------------------- | :-------------------- | :------------------------------------------- |
| `SUPER + Q`                  | `exec, $terminal`     | Launches your terminal (`kitty`).            |
| `SUPER + C`                  | `killactive,`         | Kills the active window.                     |
| `SUPER + E`                  | `exec, $fileManager`  | Launches your file manager (`kitty ranger`). |
| `SUPER + W`                  | `exec, $windowMenu`   | Opens the Rofi window menu.                  |
| `SUPER + J`                  | `togglesplit,`        | Toggles split direction in dwindle layout.   |
| `SUPER + SHIFT + F`          | `togglefloating,`     | Toggles floating mode for the active window. |
| `SUPER + F`                  | `fullscreen`          | Toggles fullscreen for the active window.    |
| `SUPER + SHIFT + Left`       | `swapwindow, l`       | Swaps the active window with the window to its left. |
| `SUPER + SHIFT + Down`       | `swapwindow, d`       | Swaps the active window with the window below it. |
| `SUPER + SHIFT + Up`         | `swapwindow, u`       | Swaps the active window with the window above it. |
| `SUPER + SHIFT + Right`      | `swapwindow, r`       | Swaps the active window with the window to its right. |
| `SUPER + CTRL + SHIFT + Left`| `movewindow, l`       | Moves the active window to the left.         |
| `SUPER + CTRL + SHIFT + Down`| `movewindow, d`       | Moves the active window down.                |
| `SUPER + CTRL + SHIFT + Up`  | `movewindow, u`       | Moves the active window up.                  |
| `SUPER + CTRL + SHIFT + Right`| `movewindow, r`       | Moves the active window to the right.        |

## Focus and Workspace Navigation

| Shortcut                     | Command/Action                 | Description                                    |
| :--------------------------- | :----------------------------- | :--------------------------------------------- |
| `SUPER + Left`               | `movefocus, l`                 | Moves focus to the window on the left.         |
| `SUPER + Right`              | `movefocus, r`                 | Moves focus to the window on the right.        |
| `SUPER + Up`                 | `movefocus, u`                 | Moves focus to the window above.               |
| `SUPER + Down`               | `movefocus, d`                 | Moves focus to the window below.               |
| `SUPER + SHIFT + Mouse Up`   | `movefocus, l`                 | Moves focus to the window on the left (mouse scroll). |
| `SUPER + SHIFT + Mouse Down` | `movefocus, r`                 | Moves focus to the window on the right (mouse scroll). |
| `SUPER + [1-9, 0]`           | `workspace, [1-9, 10]`         | Switches to the specified workspace.           |
| `CTRL + ALT + Right`         | `workspace, m+1`               | Switches to the next monitor's workspace.      |
| `CTRL + ALT + Left`          | `workspace, m-1`               | Switches to the previous monitor's workspace.  |
| `SUPER + SHIFT + [1-9, 0]`   | `movetoworkspace, [1-9, 10]`   | Moves the active window to the specified workspace. |
| `SUPER + SHIFT + L`          | `movetoworkspace, r+1`         | Moves the active window to the next right workspace (on another monitor if applicable). |
| `SUPER + SHIFT + H`          | `movetoworkspace, r-1`         | Moves the active window to the next left workspace (on another monitor if applicable). |
| `SUPER + TAB`                | `workspace, previous`          | Switches to the previously active workspace.   |
| `SUPER + CTRL + Right`       | `movewindow, mon:1`            | Moves the active window to monitor 1.          |
| `SUPER + CTRL + Left`        | `movewindow, mon:0`            | Moves the active window to monitor 0.          |
| `SUPER + Mouse Down`         | `workspace, e+1`               | Scrolls to the next workspace.                 |
| `SUPER + Mouse Up`           | `workspace, e-1`               | Scrolls to the previous workspace.             |
| `SUPER + S`                  | `togglespecialworkspace, magic`| Toggles the special workspace "magic" (scratchpad). |
| `SUPER + SHIFT + S`          | `movetoworkspace, special:magic`| Moves the active window to the "magic" special workspace. |

## Application Launchers and Utilities

| Shortcut                     | Command/Action                       | Description                                    |
| :--------------------------- | :----------------------------------- | :--------------------------------------------- |
| `SUPER + R`                  | `exec, $menu`                        | Opens the Rofi application launcher.           |
| `SUPER + SHIFT + R`          | `exec, $shellMenu`                   | Executes your custom shell menu script.        |
| `SUPER + CTRL + SHIFT + R`   | `exec, $terminalMenu`                | Executes your custom Rofi terminal history menu. |
| `SUPER + V`                  | `exec, $clipHistMenu`                | Opens the cliphist menu for clipboard history. |
| `SHIFT + 107` (Print Screen) | `exec, ~/.config/hypr/scripts/screenshot/captureAll.sh` | Takes a screenshot of the entire screen.     |
| `107` (Print Screen)         | `exec, ~/.config/hypr/scripts/screenshot/captureArea.sh` | Takes a screenshot of a selected area.       |
| `CTRL + Escape`              | `exec, gnome-system-monitor`         | Launches the GNOME System Monitor.             |

## Session Management

| Shortcut                     | Command/Action                                | Description                                        |
| :--------------------------- | :-------------------------------------------- | :------------------------------------------------- |
| `SUPER + M`                  | `exec, ~/.config/hypr/scripts/confirm-before-exit.sh exit` | Prompts for confirmation before exiting Hyprland. |
| `SUPER + SHIFT + M`          | `exec, ~/.config/hypr/scripts/confirm-before-exit.sh poweroff` | Prompts for confirmation before powering off.     |
| `SUPER + CTRL + M`           | `exec, ~/.config/hypr/scripts/confirm-before-exit.sh reboot` | Prompts for confirmation before rebooting.        |
| `SUPER + L`                  | `exec, hyprlock`                              | Locks the screen using hyprlock.                   |
| `Lid Switch`                 | `exec, hyprlock`                              | Locks the screen when the laptop lid is closed.    |

## Brightness Control

| Shortcut                     | Command/Action                                       | Description                          |
| :----------------------------- | :--------------------------------------------------- | :----------------------------------- |
| `SUPER + CTRL + 86` (Numpad's `+`) | `exec, brightnessctl --device $backlightDevice set 10%+` | Increases screen brightness by 10%.  |
| `SUPER + CTRL + 82` (Numpad's `-`) | `exec, brightnessctl --device $backlightDevice set 10%-` | Decreases screen brightness by 10%.  |

## Window Resizing and Movement (Mouse)

| Shortcut                    | Command/Action       | Description                                    |
| :-------------------------- | :------------------- | :--------------------------------------------- |
| `SUPER + LMB` (mouse:272)   | `movewindow`         | Moves the active window by dragging with the left mouse button. |
| `SUPER + RMB` (mouse:273)   | `resizewindow`       | Resizes the active window by dragging with the right mouse button. |
