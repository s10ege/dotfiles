# dotfiles

My Omarchy (Arch + Hyprland) setup. `~/.config` is the repo. The `.gitignore` is an allowlist, so only the configs listed there are tracked.
Inspired by [kunchenguid/dotfiles](https://github.com/kunchenguid/dotfiles).

## What's here

| Path | What |
|---|---|
| `CHEATSHEET.md` | Quick reference: every added tool and skill, and how to use it |
| `agents/AGENTS.md` | Global rules for every coding agent. Linked into Claude, Codex, opencode and Pi. |
| `claude/` | Claude Code `settings.json` and statusline (linked into `~/.claude`) |
| `codex/` | Codex `config.toml` and `hooks.json` (linked into `~/.codex`) |
| `no-mistakes/config.yaml` | Global no-mistakes gate config (reviewer: claude, then codex) |
| `bash/bashrc` | Linked to `~/.bashrc`. Aliases `cc` (Claude) and `co` (Codex), `y` (yazi), atuin |
| `herdr/config.toml` | herdr keys and theme |
| `hypr/`, `nvim/`, `starship.toml`, `git/`, `lazygit/`, `atuin/`, `mise/` | Tool configs |
| `packages.txt` | Extra pacman packages on top of Omarchy |
| `justfile` | `install`, `link`, `integrations`, `nm-init`, `sync` |

Shared skills live in `~/.agents/skills` (not in this repo). `just link` links each one into both `~/.claude/skills` and `~/.codex/skills`, so Claude and Codex always see the same skills.

## New machine

```bash
git clone https://github.com/s10ege/dotfiles ~/.config   # on a fresh Omarchy, merge into the existing ~/.config
cd ~/.config
just install        # pacman packages
just link           # symlinks for bash, Claude, Codex, opencode, Pi, no-mistakes, skills
just integrations   # herdr agent-state hooks
just nm-init        # no-mistakes gate in every repo with an origin
```

## Daily use

- Edit files here in place. Everything is symlinked, so changes are live.
- `just sync "message"` commits everything tracked and pushes. This recipe is for you; agents follow the stage-only-your-own-hunks rule in AGENTS.md.
- For code repos, push with `git push no-mistakes` instead of `git push origin`.
- `ccusage daily` shows Claude, Codex and Pi usage.
