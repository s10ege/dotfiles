#!/bin/sh
# Open a floating Claude "help" chat. The chat lives in a background tmux
# session called "help", so closing the popup keeps the conversation.
# Full path to claude: tmux's PATH may not include ~/.local/bin.
tmux display-popup -E -w 60% -h 60% -T ' Claude help ' \
  "TMUX= tmux new-session -A -s help -c ~/dotfiles $HOME/.local/bin/claude \; set-option -t help status off"
