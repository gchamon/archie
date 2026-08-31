-- Archie Hyprland configuration entry point.
-- Keep modules independent so a failure in one does not prevent the others
-- from loading.

require("config.environment")
require("config.appearance")
require("config.input")
require("config.rules")

local config_home = os.getenv("XDG_CONFIG_HOME") or (os.getenv("HOME") .. "/.config")
local device_path = config_home .. "/hypr/config/device.lua"
local device_loader = loadfile(device_path)
local device = device_loader and device_loader() or {}

require("config.binds")(device)
require("config.autostart")
