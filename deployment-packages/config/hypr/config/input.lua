hl.config({
  input = {
    kb_layout = "br",
    kb_variant = "abnt2",
    kb_model = "",
    kb_options = "",
    kb_rules = "",
    numlock_by_default = true,
    follow_mouse = 1,
    touchpad = {
      natural_scroll = true,
    },
    sensitivity = 0,
  },
})

hl.device({
  name = "logitech-mx-keys",
  kb_layout = "us",
  kb_variant = "intl",
})

hl.device({
  name = "mx-keys-keyboard",
  kb_layout = "us",
  kb_variant = "intl",
})
