hl.config({
  cursor = {
    no_hardware_cursors = true,
  },
  general = {
    gaps_in = 5,
    gaps_out = 20,
    border_size = 2,
    col = {
      active_border = {
        colors = { "rgba(ff30c7ee)", "rgba(00ff99ee)" },
        angle = 45,
      },
      inactive_border = "rgba(5959b4aa)",
    },
    layout = "dwindle",
    allow_tearing = false,
  },
  decoration = {
    rounding = 5,
    blur = {
      enabled = true,
      size = 3,
      passes = 1,
      vibrancy = 0.1696,
    },
    shadow = {
      enabled = true,
      range = 4,
      render_power = 3,
      color = 0xee1a1a1a,
    },
  },
  animations = {
    enabled = true,
  },
  dwindle = {
    preserve_split = true,
  },
  master = {
    new_status = "master",
  },
  misc = {
    force_default_wallpaper = 0,
  },
  ecosystem = {
    no_update_news = true,
  },
})

hl.curve("myBezier", {
  type = "bezier",
  points = { { 0.05, 0.9 }, { 0.1, 1.05 } },
})

hl.animation({ leaf = "windows", enabled = true, speed = 4, bezier = "myBezier" })
hl.animation({ leaf = "windowsOut", enabled = true, speed = 4, bezier = "default", style = "popin 90%" })
hl.animation({ leaf = "border", enabled = true, speed = 5, bezier = "default" })
hl.animation({ leaf = "borderangle", enabled = true, speed = 4, bezier = "default" })
hl.animation({ leaf = "fade", enabled = true, speed = 3, bezier = "default" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 3, bezier = "default" })

hl.gesture({
  fingers = 3,
  direction = "horizontal",
  action = "workspace",
})
