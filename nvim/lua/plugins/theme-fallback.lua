-- Without Omarchy (macOS) link.sh creates no theme.lua link, so use the closest plain match.
if vim.uv.fs_stat(vim.fn.stdpath("config") .. "/lua/plugins/theme.lua") then
	return {}
end

return {
	{
		"LazyVim/LazyVim",
		opts = {
			colorscheme = "tokyonight-night",
		},
	},
}
