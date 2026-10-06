# dotfiles

My setup for two laptops: Omarchy (Arch + Hyprland) and a 2017 Intel MacBook Pro on macOS Ventura 13. `~/.config` is the repo on both. The `.gitignore` is an allowlist, so only the configs listed there are tracked.
Inspired by [kunchenguid/dotfiles](https://github.com/kunchenguid/dotfiles).

## What's here

| Path | Where | What |
|---|---|---|
| `bootstrap.sh` | both | New-machine setup: packages, mise tools, then `link.sh`. `--link-only` skips installs. |
| `link.sh` | both | Symlinks into `~/.claude`, `~/.codex`, `~/.pi`, `~/.no-mistakes`, `~/.bashrc` and the skill dirs. Branches by OS. |
| `CHEATSHEET.md` | both | Quick reference: every added tool and skill, and how to use it |
| `agents/AGENTS.md` | both | Global rules for every coding agent. Linked into Claude, Codex, opencode and Pi. |
| `claude/` | both | Claude Code `settings.json` and statusline (linked into `~/.claude`) |
| `codex/` | both | Codex base `config.toml` and `hooks.json` (see Codex config below) |
| `no-mistakes/config.yaml` | both | Global no-mistakes gate config (reviewer: claude, then codex) |
| `bash/bashrc` | both | Linked to `~/.bashrc`. Aliases `cc` (Claude) and `co` (Codex), `y` (yazi), atuin. Uses Omarchy's rc when present, else sets up the few Omarchy defaults itself. |
| `mise/config.toml` | both | Every shared CLI tool and its version (agents, gh, node, nvim, starship, atuin, lazygit, just, rg, fd, yazi, herdr, no-mistakes, zoxide, fzf) |
| `wezterm/wezterm.lua` | both | Shared terminal config (Tokyo Night, JetBrainsMono Nerd Font) |
| `nvim/`, `starship.toml`, `git/`, `lazygit/`, `atuin/`, `herdr/` | both | Tool configs, read in place from `~/.config` |
| `hypr/` | Linux | Hyprland (read in place) |
| `packages.txt` | Linux | Extra pacman packages on top of Omarchy |
| `Brewfile` | Mac | Homebrew bash 5, bash-preexec, AeroSpace, WezTerm, Nerd Font. No shared CLIs: Homebrew on Intel is Tier 3 and ends on 2027-09-01. |
| `bash/bash_profile` | Mac | Linked to `~/.bash_profile`, sources `~/.bashrc` (Mac terminals start login shells) |
| `aerospace/aerospace.toml` | Mac | AeroSpace tiling, the Omarchy default Hyprland keys with Option for SUPER (read in place) |
| `justfile` | both | Optional task recipes; `just` comes from mise |

Shared skills live in `~/.agents/skills` (not in this repo). `link.sh` links each one into both `~/.claude/skills` and `~/.codex/skills`, so Claude and Codex always see the same skills.

## New machine

Linux (Omarchy):

```bash
git clone https://github.com/s10ege/dotfiles ~/.config   # on a fresh Omarchy, merge into the existing ~/.config
~/.config/bootstrap.sh   # pacman packages.txt, mise install, link.sh
```

Mac:

```bash
xcode-select --install   # git
git clone https://github.com/s10ege/dotfiles ~/.config
~/.config/bootstrap.sh   # Homebrew + Brewfile, mise install, link.sh
# One-time: make Homebrew bash 5 the login shell (macOS ships bash 3.2)
echo /usr/local/bin/bash | sudo tee -a /etc/shells
chsh -s /usr/local/bin/bash
```

Then open a new terminal (WezTerm), start AeroSpace once and allow it in System Settings > Privacy & Security > Accessibility.

Both, optional:

```bash
just integrations   # herdr agent-state hooks
just nm-init        # no-mistakes gate in every repo with an origin
```

## How things fit

- **mise and PATH on Linux.** mise now provides the shared CLIs on both machines, but the pacman/Omarchy copies stay installed on Linux. Interactive shells run `mise activate`, which puts mise's versions first. Non-interactive login shells (ssh commands, the Hyprland session) get Omarchy's PATH, where `/usr/bin` comes before `~/.local/share/mise/shims`, so they keep the pacman copies.
- **Codex config.** Codex writes machine state into `~/.codex/config.toml` (project trust, hook hashes, notices). That file is therefore a real, untracked file, not a link: `link.sh` rebuilds it as `codex/config.toml` (the tracked base) plus the machine tables it finds in the existing file. Change shared Codex settings in `codex/config.toml` and rerun `link.sh`; settings changed inside Codex are overwritten on the next link.
- **Claude settings** stay a plain link: they are your own choices, and the herdr hook calls its script through `$HOME`, so the file works on both machines. `just integrations` installs only the hook scripts for Claude and Codex so herdr does not add a second, absolute-path hook.
- **nvim theme.** On Omarchy `link.sh` links `nvim/lua/plugins/theme.lua` (untracked) to the current Omarchy theme, and the theme switcher plugins load. Without Omarchy, nvim uses tokyonight-night.

## Daily use

- Edit files here in place. Everything is symlinked, so changes are live.
- `just sync "message"` stages changes to tracked files only (`git add -u`), prints what will be committed, then commits and pushes. Add new files with `git add` first. This recipe is for you; agents follow the stage-only-your-own-hunks rule in AGENTS.md.
- For code repos, push with `git push no-mistakes` instead of `git push origin`.
- `ccusage daily` shows Claude, Codex and Pi usage.
