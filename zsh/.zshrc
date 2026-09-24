   # History
   HISTSIZE=10000
   SAVEHIST=10000
   HISTFILE=~/.zsh_history

   # Plugins
   source /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh
   source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

   # Prompt
   eval "$(starship init zsh)"

# Neovim
export PATH="/opt/nvim-linux-x86_64/bin:$HOME/.local/bin:$PATH"
export EDITOR=nvim
alias vim=nvim
alias vi=nvim
setopt interactive_comments
