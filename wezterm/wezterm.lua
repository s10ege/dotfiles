-- Shared terminal for Omarchy and macOS. Look matches the Omarchy Tokyo Night theme and foot setup.
local wezterm = require("wezterm")
local config = wezterm.config_builder()
local is_mac = wezterm.target_triple:find("darwin") ~= nil

config.color_scheme = "Tokyo Night"
config.font = wezterm.font("JetBrainsMono Nerd Font")
config.font_size = is_mac and 13 or 9
config.window_padding = { left = 14, right = 14, top = 14, bottom = 14 }
config.window_decorations = "RESIZE"
config.hide_tab_bar_if_only_one_tab = true
config.scrollback_lines = 10000
config.audible_bell = "Disabled"

-- Option is Alt/Meta in the shell (AeroSpace takes its Option bindings before the terminal sees them).
config.send_composed_key_when_left_alt_is_pressed = false
config.send_composed_key_when_right_alt_is_pressed = false

config.keys = {
	-- Send Shift+Return as CSI-u so TUIs (Claude Code, Codex) can tell it from Return.
	{ key = "Enter", mods = "SHIFT", action = wezterm.action.SendString("\x1b[13;2u") },
}

return config
