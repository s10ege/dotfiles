local wezterm = require("wezterm")
local config = wezterm.config_builder()

-- Open Ubuntu (WSL) instead of PowerShell
config.default_domain = "WSL:Ubuntu"

-- Look
config.font = wezterm.font("JetBrainsMono Nerd Font")
config.font_size = 12
config.color_scheme = "Catppuccin Mocha"
config.window_background_opacity = 0.95
config.window_padding = { left = 8, right = 8, top = 8, bottom = 8 }
config.hide_tab_bar_if_only_one_tab = true

-- Right-click pastes
config.mouse_bindings = {
  {
    event = { Down = { streak = 1, button = "Right" } },
    mods = "NONE",
    action = wezterm.action.PasteFrom("Clipboard"),
  },
}

return config
