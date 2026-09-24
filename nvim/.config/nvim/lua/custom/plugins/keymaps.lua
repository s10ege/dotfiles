-- Space + Enter: open the floating Claude helper (see tmux/claude-help.sh)
vim.keymap.set('n', '<leader><CR>', function()
  if not vim.env.TMUX then
    return vim.notify('Claude helper only works inside tmux', vim.log.levels.WARN)
  end
  vim.fn.jobstart { vim.fn.expand '~/.config/tmux/claude-help.sh' }
end, { desc = 'Ask Claude helper' })

return {}
