# Dotfiles tasks. Run from anywhere with: just -f ~/.config/justfile <recipe>

config := env_var('HOME') / ".config"

# list recipes
default:
    @just --list --justfile {{justfile()}}

# install extra pacman packages from packages.txt
install:
    grep -vE '^\s*(#|$)' {{config}}/packages.txt | sudo pacman -S --needed -

# (re)create symlinks from agent/home dirs into this repo, and share skills with Claude and Codex
link:
    #!/usr/bin/env bash
    set -euo pipefail
    c={{config}}
    ln -sfn "$c/bash/bashrc"              ~/.bashrc
    ln -sfn "$c/agents/AGENTS.md"         ~/.claude/CLAUDE.md
    ln -sfn "$c/claude/settings.json"     ~/.claude/settings.json
    ln -sfn "$c/claude/statusline.sh"     ~/.claude/statusline.sh
    ln -sfn "$c/agents/AGENTS.md"         ~/.codex/AGENTS.md
    ln -sfn "$c/codex/config.toml"        ~/.codex/config.toml
    ln -sfn "$c/codex/hooks.json"         ~/.codex/hooks.json
    ln -sfn "$c/agents/AGENTS.md"         "$c/opencode/AGENTS.md"
    mkdir -p ~/.pi/agent ~/.no-mistakes
    ln -sfn "$c/agents/AGENTS.md"         ~/.pi/agent/AGENTS.md
    ln -sfn "$c/no-mistakes/config.yaml"  ~/.no-mistakes/config.yaml
    mkdir -p ~/.agents/skills ~/.claude/skills ~/.codex/skills
    for s in ~/.agents/skills/*/; do
      n=$(basename "$s")
      for d in ~/.claude/skills ~/.codex/skills; do
        [ -e "$d/$n" ] && [ ! -L "$d/$n" ] && { echo "skip $d/$n (real dir)"; continue; }
        ln -sfn "$HOME/.agents/skills/$n" "$d/$n"
      done
    done
    echo "linked"

# install herdr agent-state hooks for every agent
integrations:
    for a in claude codex opencode pi; do herdr integration install $a; done

# gate every repo under ~/Projects and ~/.config with no-mistakes (repos need an origin remote)
nm-init:
    #!/usr/bin/env bash
    for r in {{config}} ~/Projects/*/; do
      git -C "$r" remote get-url origin >/dev/null 2>&1 || { echo "skip $r (no origin)"; continue; }
      (cd "$r" && no-mistakes init) && echo "gated $r"
    done

# commit and push dotfiles changes
sync msg="update dotfiles":
    git -C {{config}} add -A
    git -C {{config}} commit -m "{{msg}}" || true
    git -C {{config}} push
