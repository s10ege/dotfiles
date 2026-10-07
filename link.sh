#!/usr/bin/env bash
# (Re)create symlinks from agent/home dirs into this repo, and share skills with Claude and Codex.
# Safe to rerun. Called by bootstrap.sh and `just link`. Keep it bash 3.2 compatible (macOS).
set -euo pipefail
c=$(cd "$(dirname "$0")" && pwd -P)

mkdir -p ~/.claude ~/.codex ~/.pi/agent ~/.no-mistakes
ln -sfn "$c/bash/bashrc"              ~/.bashrc
ln -sfn "$c/agents/AGENTS.md"         ~/.claude/CLAUDE.md
ln -sfn "$c/claude/settings.json"     ~/.claude/settings.json
ln -sfn "$c/claude/statusline.sh"     ~/.claude/statusline.sh
ln -sfn "$c/agents/AGENTS.md"         ~/.codex/AGENTS.md
ln -sfn "$c/codex/hooks.json"         ~/.codex/hooks.json
# Keep machine-generated default.rules intact; load shared Git prohibitions alongside it.
mkdir -p ~/.codex/rules
ln -sfn "$c/codex/rules/git-guard.rules" ~/.codex/rules/git-guard.rules
ln -sfn ../agents/AGENTS.md           "$c/opencode/AGENTS.md"
ln -sfn "$c/agents/AGENTS.md"         ~/.pi/agent/AGENTS.md
ln -sfn "$c/no-mistakes/config.yaml"  ~/.no-mistakes/config.yaml

case $(uname -s) in
  Linux)
    # Omarchy theme for nvim; nvim falls back to tokyonight when this link is absent.
    t="$HOME/.local/state/omarchy/current/theme/neovim.lua"
    [ -e "$t" ] && ln -sfn "$t" "$c/nvim/lua/plugins/theme.lua"
    ;;
  Darwin)
    # Terminal apps start login shells, which read ~/.bash_profile instead of ~/.bashrc.
    ln -sfn "$c/bash/bash_profile"    ~/.bash_profile
    ;;
esac

# Codex rewrites config.toml with machine state (project trust, hook hashes, notices).
# ~/.codex/config.toml is a real, untracked file: the tracked base plus the machine tables Codex already wrote.
cfg=~/.codex/config.toml
pick='/^\[/ { keep = /^\[(projects|hooks\.state|notice|tui\.model_availability_nux)[].]/ } keep'
state=""
[ -e "$cfg" ] && state=$(awk "$pick" "$cfg")
# One-time migration: this file used to be a symlink into the repo, so pulling the bare
# base dropped Codex's state. Recover it from the newest committed version that had any.
if [ -L "$cfg" ] && [ -z "$state" ]; then
  for r in $(git -C "$c" rev-list HEAD -- codex/config.toml 2>/dev/null); do
    state=$(git -C "$c" show "$r:codex/config.toml" | awk "$pick")
    [ -z "$state" ] || break
  done
fi
{ cat "$c/codex/config.toml"; [ -z "$state" ] || printf '\n%s\n' "$state"; } > "$cfg.tmp"
mv -f "$cfg.tmp" "$cfg"

mkdir -p ~/.agents/skills ~/.claude/skills ~/.codex/skills
# Repo-owned skills join the shared skill directory; keep third-party skills in place.
for s in "$c"/agents/skills/*/; do
  [ -d "$s" ] || continue
  n=$(basename "$s")
  d="$HOME/.agents/skills/$n"
  [ -e "$d" ] && [ ! -L "$d" ] && { echo "skip $d (real dir)"; continue; }
  ln -sfn "$c/agents/skills/$n" "$d"
done
for s in ~/.agents/skills/*/; do
  [ -d "$s" ] || continue
  n=$(basename "$s")
  for d in ~/.claude/skills ~/.codex/skills; do
    [ -e "$d/$n" ] && [ ! -L "$d/$n" ] && { echo "skip $d/$n (real dir)"; continue; }
    ln -sfn "$HOME/.agents/skills/$n" "$d/$n"
  done
done
echo "linked"
