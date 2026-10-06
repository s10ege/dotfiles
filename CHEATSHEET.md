# Cheatsheet

## Agents
| What | How |
|---|---|
| Claude | `cc` |
| Codex | `co` |
| Global rules (both) | edit `~/.config/agents/AGENTS.md` |
| Usage / cost | `ccusage daily` · `ccusage blocks` |

**Claude + Codex on one repo:** give each one its own worktree (`codex --worktree`, or `herdr worktree ...`). They're told to stage only their own files.

## Skills (Claude and Codex)
| Skill | What it does | Use |
|---|---|---|
| handoff | Summarizes the session so a fresh one (or the other agent) can continue | `/handoff` |
| i-have-adhd | Answer-first, short, numbered replies | `/i-have-adhd` · "stop adhd mode" |
| ponytail | Simplest possible solution, no over-engineering | "ponytail" / "be lazy" (auto on coding tasks) |
| Superpowers | Brainstorm → plan → TDD → review workflow | "brainstorm this" · `/superpowers:...` (asks before spawning subagents) |
| lavish | Opens plans and diffs as HTML you can annotate | "show it in lavish" |
| no-mistakes | Runs the review pipeline for you | `/no-mistakes` |

## Agent tools
| Tool | What | Use |
|---|---|---|
| herdr | Workspaces + each agent's live state in the sidebar | `herdr` · prefix `ctrl+space` |
| no-mistakes | AI review, tests and lint before code reaches GitHub | `git push no-mistakes <branch>` · `no-mistakes status` |
| firstmate | One agent that runs a crew of agents | `cd ~/Projects/firstmate && claude` |
| SkillSpector | Checks a skill for security issues before you install it | `skillspector scan <dir> --no-llm` |

## Terminal tools
| Tool | What | Use |
|---|---|---|
| atuin | Searchable shell history | `Ctrl+R` |
| yazi | File manager (cds you where you quit) | `y` · `q` to quit |
| gitlogue | Replays git history as animated typing | `gitlogue` in a repo |
| kondo | Deletes build junk (node_modules, .venv) | `kondo ~/Projects` |

## Dotfiles (`~/.config`, repo `s10ege/dotfiles`, Omarchy and Mac)
| Task | Command |
|---|---|
| New machine (Linux or Mac) | clone to `~/.config`, then `~/.config/bootstrap.sh` (see README) |
| Mac, once: bash 5 as login shell | `echo /usr/local/bin/bash \| sudo tee -a /etc/shells && chsh -s /usr/local/bin/bash` |
| Fix broken symlinks / share a new skill | `~/.config/link.sh` (or `just -f ~/.config/justfile link`) |
| Update shared CLI tools (both) | `mise up` |
| Install packages | Linux: `~/.config/bootstrap.sh` (pacman `packages.txt`) · Mac: `brew bundle --file ~/.config/Brewfile` |
| Save + push changes to tracked files | `just -f ~/.config/justfile sync "msg"` (`git add` new files first) |
| Gate a new repo with no-mistakes | `just -f ~/.config/justfile nm-init` |
| Add a skill | clone it into `~/.agents/src/`, link its folder into `~/.agents/skills/`, then run `link.sh` |

## Mac window manager (AeroSpace, Option = Omarchy's SUPER)
| What | Keys |
|---|---|
| Terminal / browser / Finder | `Opt+Return` · `Opt+Shift+Return` · `Opt+Shift+F` |
| Close / full screen / float / split | `Opt+W` · `Opt+F` · `Opt+T` · `Opt+J` |
| Focus / swap window | `Opt+Arrows` · `Opt+Shift+Arrows` |
| Workspace / move window there | `Opt+1..0` · `Opt+Shift+1..0` |
| Next / previous / former workspace | `Opt+Tab` · `Opt+Shift+Tab` · `Opt+Ctrl+Tab` |
| Resize | `Opt+-` / `Opt+=` (width) · `Opt+Shift+-` / `Opt+Shift+=` (height) |
