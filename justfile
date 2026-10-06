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
    {{justfile_directory()}}/link.sh

# install herdr agent-state hooks for every agent
integrations:
    #!/usr/bin/env bash
    set -euo pipefail
    # The tracked Claude/Codex hooks call these scripts via $HOME; installing straight into
    # ~/.claude and ~/.codex would add a second, absolute-path hook to the tracked files.
    t=$(mktemp -d)
    mkdir -p "$t/.claude" "$t/.codex"
    HOME=$t herdr integration install claude
    HOME=$t herdr integration install codex
    mkdir -p ~/.claude/hooks
    cp "$t/.claude/hooks/herdr-agent-state.sh" ~/.claude/hooks/
    cp "$t/.codex/herdr-agent-state.sh" ~/.codex/
    rm -rf "$t"
    for a in opencode pi; do herdr integration install $a; done

# gate every repo of mine (origin on github.com/s10ege) under ~/Projects and ~/.config with no-mistakes
nm-init:
    #!/usr/bin/env bash
    for r in {{config}} ~/Projects/*/; do
      url=$(git -C "$r" remote get-url origin 2>/dev/null) || { echo "skip $r (no origin)"; continue; }
      [[ "$url" == *github.com[:/]s10ege/* ]] || { echo "skip $r (not my repo)"; continue; }
      (cd "$r" && no-mistakes init) && echo "gated $r"
    done

# commit and push tracked files; /dotfiles-sync reviews groups and translates for the other OS
sync msg="update dotfiles":
    git -C {{config}} add -u
    git -C {{config}} diff --cached --stat
    git -C {{config}} commit -m "{{msg}}" || true
    git -C {{config}} push
