# dotfiles

My setup for two laptops: Omarchy (Arch + Hyprland) and a 2017 Intel MacBook Pro on macOS Ventura 13. `~/.config` is the repo on both. The `.gitignore` is an allowlist, so only the configs listed there are tracked.
Inspired by [kunchenguid/dotfiles](https://github.com/kunchenguid/dotfiles).

## What's here

| Path | Where | What |
|---|---|---|
| `bootstrap.sh` | both | New-machine setup: packages, mise tools, then `link.sh`. `--link-only` skips installs. |
| `link.sh` | both | Symlinks into `~/.claude`, `~/.codex`, `~/.pi`, `~/.no-mistakes`, `~/.bashrc` and the skill dirs. Branches by OS. |
| `CHEATSHEET.md` | both | Quick reference: every added tool and skill, and how to use it |
| `agents/skills/` | both | Repo-owned skills, starting with `dotfiles-sync`; linked through `~/.agents/skills` into Claude and Codex |
| `agents/AGENTS.md` | both | Global rules for every coding agent. Linked into Claude, Codex, opencode and Pi. |
| `claude/` | both | Claude Code `settings.json`, statusline and Bash Git guard |
| `codex/` | both | Codex base `config.toml`, `hooks.json` and shared Git guard rules (see Codex config below) |
| `no-mistakes/config.yaml` | both | Global no-mistakes gate config (reviewer: claude, then codex) |
| `bash/bashrc` | both | Linked to `~/.bashrc`. Aliases `cc` (Claude) and `co` (Codex), `y` (yazi), atuin. Uses Omarchy's rc when present, else sets up the few Omarchy defaults itself. |
| `mise/config.toml` | both | Every shared CLI tool and its version (agents, gh, node, nvim, starship, atuin, lazygit, just, rg, fd, yazi, herdr, no-mistakes, zoxide, fzf, gitleaks) |
| `wezterm/wezterm.lua` | both | Shared terminal config (Tokyo Night, JetBrainsMono Nerd Font) |
| `nvim/`, `starship.toml`, `git/`, `lazygit/`, `atuin/`, `herdr/` | both | Tool configs, read in place from `~/.config` |
| `hypr/` | Linux | Hyprland (read in place) |
| `packages.txt` | Linux | Extra pacman packages on top of Omarchy |
| `Brewfile` | Mac | Homebrew bash 5, bash-preexec, AeroSpace, WezTerm, Nerd Font. No shared CLIs: Homebrew on Intel is Tier 3 and ends on 2027-09-01. |
| `bash/bash_profile` | Mac | Linked to `~/.bash_profile`, sources `~/.bashrc` (Mac terminals start login shells) |
| `aerospace/aerospace.toml` | Mac | AeroSpace tiling, the Omarchy default Hyprland keys with Option for SUPER (read in place) |
| `justfile` | both | Optional task recipes; `just` comes from mise |

Repo-owned skills live in `agents/skills/`; `link.sh` links each into `~/.agents/skills`, then into both `~/.claude/skills` and `~/.codex/skills`. Existing third-party skills in `~/.agents/skills` stay in place. A real directory with the same name is preserved and reported as skipped.

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
- **Codex config.** Codex writes machine state into `~/.codex/config.toml` (project trust, hook hashes, notices). That file is therefore a real, untracked file, not a link: `link.sh` rebuilds it as `codex/config.toml` (the tracked base) plus the machine tables it finds in the existing file. Change shared Codex settings in `codex/config.toml` and rerun `link.sh`; settings changed inside Codex are overwritten on the next link. `link.sh` links `codex/rules/git-guard.rules` alongside the machine-owned `~/.codex/rules/default.rules`, preserving existing approvals.
- **Claude settings** stay a plain link: they are your own choices, and the herdr hook calls its script through `$HOME`, so the file works on both machines. `just integrations` installs only the hook scripts for Claude and Codex so herdr does not add a second, absolute-path hook.
- **nvim theme.** On Omarchy `link.sh` links `nvim/lua/plugins/theme.lua` (untracked) to the current Omarchy theme, and the theme switcher plugins load. Without Omarchy, nvim uses tokyonight-night.

## Daily use

- Edit files here in place. Everything is symlinked, so changes are live.
- `/dotfiles-sync` in Claude or `$dotfiles-sync` in Codex reviews all changes by topic, asks yes/no per group, scans approved hunks with gitleaks, commits and pushes. Tool noise is skipped by default. A subagent proposes equivalents for the other OS; you review them before a separate commit. After pushing, it pulls and applies on the peer over SSH. Use `/dotfiles-sync apply` or `$dotfiles-sync apply` on either laptop to pull and apply incoming changes locally. Run `link.sh` once after first pulling this skill so both agents discover it.
- `just sync "message"` stages changes to tracked files only (`git add -u`), prints what will be committed, then commits and pushes. Add new files with `git add` first. This recipe is for you; agents follow the stage-only-your-own-hunks rule in AGENTS.md.
- For code repos, push with `git push no-mistakes` instead of `git push origin`.
- `ccusage daily` shows Claude, Codex and Pi usage.

## Connect the laptops (Tailscale + SSH)

Perform this setup yourself on both laptops. The repo must be at `~/.config`
with an upstream configured on each. We use ordinary SSH over Tailscale.

1. On Omarchy, install and log in following [Tailscale's Linux instructions](https://tailscale.com/docs/install/linux):

   ```bash
   sudo pacman -S --needed tailscale openssh
   sudo systemctl enable --now tailscaled
   sudo tailscale up
   sudo systemctl enable --now sshd
   ```

2. On the Intel Mac (Ventura 13.7.8), install the [Tailscale macOS app](https://tailscale.com/docs/install/mac), open it, and log into the same tailnet. Enable [Remote Login](https://support.apple.com/guide/mac-help/allow-a-remote-computer-to-access-your-mac-mchlp1066/13.0/mac/13.0) in System Settings > General > Sharing, allowing your account.
3. Exchange public SSH keys in both directions. Reuse an existing key or generate one with `ssh-keygen -t ed25519`. Copy that laptop's `.pub` file contents into `~/.ssh/authorized_keys` on the other, without replacing existing keys. On each destination, run `mkdir -p ~/.ssh`, `chmod 700 ~/.ssh`, and `chmod 600 ~/.ssh/authorized_keys` after adding the key. Never copy the private key. Find each laptop's Tailscale host name or `100.x.y.z` address in the Tailscale device list.
4. On **each** laptop, write the other laptop's SSH destination:

   ```bash
   mkdir -p ~/.config/agents/local
   printf '%s\n' 'username@other-laptop.tailnet-name.ts.net' > ~/.config/agents/local/peer
   ssh username@other-laptop.tailnet-name.ts.net true
   ```

   Replace the example with the peer's actual username and Tailscale name/IP.
   The peer file is gitignored: exactly one line containing `user@host` or an
   SSH config alias, no comments, options or shell syntax. Use letters, digits,
   dots, underscores and hyphens, with one optional `@`; no leading `-`.
   Verify the host-key fingerprint on first connection. SSH must find the key
   without an interactive password prompt (unlock it in your SSH agent).

After a push, the skill invokes the peer's `agents/skills/dotfiles-sync/apply.sh`
with a five-second SSH connection timeout. If the peer is offline, run apply mode
there next time. If SSH connected but apply failed, review the printed error.
The helper refuses local changes and pulls only fast-forward updates. It runs
`link.sh` for link/agent/home-config changes, `mise install` for the mise manifest,
Mac Brewfile installs without upgrades, and only the changed OS's window-manager
reload (AeroSpace validates first). It does not install Linux `packages.txt`
automatically. If a command fails after pulling, fix it and rerun the printed
command; another pull has no diff to replay. New home-directory links belong in
`link.sh`, so their introduction selects the link step.

Validate locally with `python3 agents/skills/dotfiles-sync/test.py` (temporary
homes, a bare remote and two clones, with install/reload commands stubbed).
