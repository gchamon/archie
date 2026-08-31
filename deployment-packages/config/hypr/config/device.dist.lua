-- Machine-specific settings. Copy this file to device.lua and customize it.
--
-- hl.env("AQ_DRM_DEVICES", "/dev/dri/card0:/dev/dri/card1")
-- hl.monitor({
--   output = "eDP-1",
--   mode = "1920x1080@144.14900",
--   position = "0x300",
--   scale = 1,
-- })

return {
  -- Set this when brightnessctl must address a specific backlight device.
  -- backlight_device = "amdgpu_bl0",
}
