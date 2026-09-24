   # History
   HISTSIZE=10000
   SAVEHIST=10000
   HISTFILE=~/.zsh_history

   # Plugins
   source /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh
   source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

   # Prompt
   eval "$(starship init zsh)"
