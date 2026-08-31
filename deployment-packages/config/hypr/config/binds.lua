return function(device)
  local main_mod = "SUPER"
  local terminal = "kitty"
  local file_manager = "kitty ranger $HOME"
  local menu = "rofi -show drun -show-icons"
  local window_menu = "rofi -show window -show-icons"
  local shell_menu = "~/.config/hypr/scripts/launch-shell-menu.sh"
  local terminal_menu = 'kitty bash -c "$(~/.config/hypr/scripts/launch-rofi-frece.sh terminal)"'
  local clip_hist_menu = "cliphist list | rofi -dmenu | cliphist decode | wl-copy"
  local brightnessctl = "brightnessctl"

  if device.backlight_device then
    brightnessctl = brightnessctl .. " --device " .. device.backlight_device
  end

  hl.bind(main_mod .. " + Q", hl.dsp.exec_cmd(terminal))
  hl.bind(main_mod .. " + C", hl.dsp.window.close())
  hl.bind(main_mod .. " + M", hl.dsp.exec_cmd("~/.config/hypr/scripts/confirm-before-exit.sh exit"))
  hl.bind(main_mod .. " + SHIFT + M", hl.dsp.exec_cmd("~/.config/hypr/scripts/confirm-before-exit.sh poweroff"))
  hl.bind(main_mod .. " + CTRL + M", hl.dsp.exec_cmd("~/.config/hypr/scripts/confirm-before-exit.sh reboot"))
  hl.bind("XF86PowerOff", hl.dsp.exec_cmd("~/.config/hypr/scripts/confirm-before-exit.sh poweroff"))
  hl.bind(main_mod .. " + CTRL + ALT + R", hl.dsp.exec_cmd("hyprctl reload"))
  hl.bind(main_mod .. " + E", hl.dsp.exec_cmd(file_manager))
  hl.bind(main_mod .. " + R", hl.dsp.exec_cmd(menu))
  hl.bind(main_mod .. " + W", hl.dsp.exec_cmd(window_menu))
  hl.bind(main_mod .. " + SHIFT + R", hl.dsp.exec_cmd(shell_menu))
  hl.bind(main_mod .. " + CTRL + SHIFT + R", hl.dsp.exec_cmd(terminal_menu))
  hl.bind(main_mod .. " + V", hl.dsp.exec_cmd(clip_hist_menu))
  hl.bind(main_mod .. " + P", hl.dsp.window.pseudo())
  hl.bind(main_mod .. " + J", hl.dsp.layout("togglesplit"))
  hl.bind(main_mod .. " + SHIFT + J", hl.dsp.layout("swapsplit"))

  hl.bind(main_mod .. " + left", hl.dsp.focus({ direction = "left" }))
  hl.bind(main_mod .. " + right", hl.dsp.focus({ direction = "right" }))
  hl.bind(main_mod .. " + up", hl.dsp.focus({ direction = "up" }))
  hl.bind(main_mod .. " + down", hl.dsp.focus({ direction = "down" }))
  hl.bind(main_mod .. " + SHIFT + mouse_up", hl.dsp.focus({ direction = "left" }))
  hl.bind(main_mod .. " + SHIFT + mouse_down", hl.dsp.focus({ direction = "right" }))

  hl.bind(main_mod .. " + 1", hl.dsp.focus({ workspace = 1 }))
  hl.bind(main_mod .. " + 2", hl.dsp.focus({ workspace = 2 }))
  hl.bind(main_mod .. " + 3", hl.dsp.focus({ workspace = 3 }))
  hl.bind(main_mod .. " + 4", hl.dsp.focus({ workspace = 4 }))
  hl.bind(main_mod .. " + 5", hl.dsp.focus({ workspace = 5 }))
  hl.bind(main_mod .. " + 6", hl.dsp.focus({ workspace = 6 }))
  hl.bind(main_mod .. " + 7", hl.dsp.focus({ workspace = 7 }))
  hl.bind(main_mod .. " + 8", hl.dsp.focus({ workspace = 8 }))
  hl.bind(main_mod .. " + 9", hl.dsp.focus({ workspace = 9 }))
  hl.bind(main_mod .. " + 0", hl.dsp.focus({ workspace = 10 }))
  hl.bind("CTRL + ALT + right", hl.dsp.focus({ workspace = "m+1" }))
  hl.bind("CTRL + ALT + left", hl.dsp.focus({ workspace = "m-1" }))
  hl.bind("CTRL + ALT + equal", hl.dsp.focus({ workspace = "r+1" }))

  hl.bind(main_mod .. " + SHIFT + 1", hl.dsp.window.move({ workspace = 1 }))
  hl.bind(main_mod .. " + SHIFT + 2", hl.dsp.window.move({ workspace = 2 }))
  hl.bind(main_mod .. " + SHIFT + 3", hl.dsp.window.move({ workspace = 3 }))
  hl.bind(main_mod .. " + SHIFT + 4", hl.dsp.window.move({ workspace = 4 }))
  hl.bind(main_mod .. " + SHIFT + 5", hl.dsp.window.move({ workspace = 5 }))
  hl.bind(main_mod .. " + SHIFT + 6", hl.dsp.window.move({ workspace = 6 }))
  hl.bind(main_mod .. " + SHIFT + 7", hl.dsp.window.move({ workspace = 7 }))
  hl.bind(main_mod .. " + SHIFT + 8", hl.dsp.window.move({ workspace = 8 }))
  hl.bind(main_mod .. " + SHIFT + 9", hl.dsp.window.move({ workspace = 9 }))
  hl.bind(main_mod .. " + SHIFT + 0", hl.dsp.window.move({ workspace = 10 }))
  hl.bind(main_mod .. " + SHIFT + L", hl.dsp.window.move({ workspace = "r+1" }))
  hl.bind(main_mod .. " + SHIFT + H", hl.dsp.window.move({ workspace = "r-1" }))
  hl.bind(main_mod .. " + TAB", hl.dsp.focus({ workspace = "previous" }))

  hl.bind(main_mod .. " + CTRL + right", hl.dsp.window.move({ monitor = "1" }))
  hl.bind(main_mod .. " + CTRL + left", hl.dsp.window.move({ monitor = "0" }))

  hl.bind(main_mod .. " + SHIFT + F", hl.dsp.window.float({ action = "toggle" }))
  hl.bind(main_mod .. " + F", hl.dsp.window.fullscreen({ action = "toggle" }))

  hl.bind(main_mod .. " + SHIFT + left", hl.dsp.window.swap({ direction = "left" }))
  hl.bind(main_mod .. " + SHIFT + down", hl.dsp.window.swap({ direction = "down" }))
  hl.bind(main_mod .. " + SHIFT + up", hl.dsp.window.swap({ direction = "up" }))
  hl.bind(main_mod .. " + SHIFT + right", hl.dsp.window.swap({ direction = "right" }))

  hl.bind(main_mod .. " + CTRL + SHIFT + left", hl.dsp.window.move({ direction = "left" }))
  hl.bind(main_mod .. " + CTRL + SHIFT + down", hl.dsp.window.move({ direction = "down" }))
  hl.bind(main_mod .. " + CTRL + SHIFT + up", hl.dsp.window.move({ direction = "up" }))
  hl.bind(main_mod .. " + CTRL + SHIFT + right", hl.dsp.window.move({ direction = "right" }))

  hl.bind(main_mod .. " + S", hl.dsp.workspace.toggle_special("magic"))
  hl.bind(main_mod .. " + SHIFT + S", hl.dsp.window.move({ workspace = "special:magic" }))
  hl.bind(main_mod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
  hl.bind(main_mod .. " + mouse_up", hl.dsp.focus({ workspace = "e-1" }))

  -- Avoid code:N bindings: affected Hyprland Lua releases match KEY_UNKNOWN events.
  hl.bind("SHIFT + Print", hl.dsp.exec_cmd("~/.config/hypr/scripts/screenshot/captureAll.sh"))
  hl.bind("Print", hl.dsp.exec_cmd("~/.config/hypr/scripts/screenshot/captureArea.sh"))
  hl.bind(main_mod .. " + mouse:272", hl.dsp.window.drag(), { mouse = true })
  hl.bind(main_mod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })

  hl.bind(main_mod .. " + L", hl.dsp.exec_cmd("hyprlock"))
  hl.bind("switch:on:Lid Switch", hl.dsp.exec_cmd("~/.config/hypr/scripts/handle-lid-event.sh close"), { locked = true })
  hl.bind("switch:off:Lid Switch", hl.dsp.exec_cmd("~/.config/hypr/scripts/handle-lid-event.sh open"), { locked = true })
  hl.bind("CTRL + Escape", hl.dsp.exec_cmd("gnome-system-monitor"))
  hl.bind(main_mod .. " + CTRL + S", hl.dsp.dpms({ action = "toggle" }))

  hl.bind(main_mod .. " + CTRL + KP_Add", hl.dsp.exec_cmd(brightnessctl .. " set 10%+"))
  hl.bind(main_mod .. " + CTRL + KP_Subtract", hl.dsp.exec_cmd(brightnessctl .. " set 10%-"))
  hl.bind("XF86MonBrightnessUp", hl.dsp.exec_cmd(brightnessctl .. " set 10%+"))
  hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd(brightnessctl .. " set 10%-"))
end
