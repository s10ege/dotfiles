---
name: vps-run
description: Execute an agreed written plan unattended on the VPS using Claude and Codex, with durable tmux sessions and subscription quota recovery.
disable-model-invocation: true
---

# VPS run

User-invoked only: `/vps-run` in Claude or `$vps-run` in Codex. Invoking this skill authorizes preparing a run, not silently choosing its plan or launching a large crew. Once launch choices are settled, execute without further permission prompts. Ordinary project requests remain in their current session.

## Prepare and launch

1. Read the written plan and project instructions. Preserve its decisions, scope, testing, delivery process and existing owner-only boundaries. Discover the target repo and current branch rather than assuming this chat's working directory is the target. Check existing VPS jobs before launching duplicate work.
2. Resolve the remote account and tools. On this setup, development uses `jhbuild@152.228.174.33`; `jobhunt-vps` is the production `ubuntu` account and is not the build destination. Use `ssh -F ~/.ssh/config` to avoid the system SSH config permission error. The build tools need `PATH="$HOME/.npm-global/bin:$HOME/.local/bin:$PATH"` in noninteractive SSH shells. Verify `python3`, `tmux`, `claude`, `codex`, `quota-axi`, and the project's delivery tools. Use native vendor login status commands, never inspect credential files. Preserve the existing `fm` Firstmate crew and its state; these runs use separate `vps-*` sessions.
3. Settle missing launch choices together in one round: plan and related issues, VPS repo/ref, initial provider, models/effort and stronger-model escalation options, maximum concurrent workers, and completion/delivery criteria. Reuse values already supplied. Explain proposed concurrency before launching a crew. The user grants implementation, commits, pushes and merges under the project workflow; additional cloud spend and owner-only project actions remain outside that grant. Use available Claude and Codex subscription allowances, switch when exhausted, and wait for resets when both are exhausted. Paid API fallback and vendor extra-usage purchases stay disabled; confirm account-level paid overflow is disabled before a production run. Do not enable it or read API credentials.
4. Use one isolated worktree per coding worker, including the supervisor if it also codes. Prefer the installed `herdr worktree` interface where available; otherwise use `git worktree add` on a new branch. Inspect dirty work and preserve it. For a review or test-only plan, an appropriate existing isolated checkout can suffice. Move the approved plan and needed input artifacts to the VPS without copying secrets. Keep runtime files outside tracked project files.
5. Write a concrete brief on the VPS, then launch the installed helper below. A brief includes the plan's path/content, exact issues, repo/ref, worker limit, allowed models and escalation choices, tests, delivery authority and completion criteria. Workers may launch either Claude or Codex and choose settings within those choices. Record the decision policy from the next section in each worker brief. Every worker starts in bypass-permissions mode.

The shared installation is `~/.agents/skills/vps-run`, linked into both vendor skill directories. When invoked from a laptop, verify the same installation on the VPS; transfer this skill directory if absent. Never run a global dotfiles linker just to install this skill.

Run on the VPS, using model/effort flags only for the agreed values:

```bash
export PATH="$HOME/.npm-global/bin:$HOME/.local/bin:$PATH"
python3 ~/.agents/skills/vps-run/scripts/run.py start \
  --name <unique-run-name> --cwd <absolute-isolated-checkout> \
  --brief <absolute-brief-file> --first <claude-or-codex>
```

`start --help` lists `--claude-model`, `--claude-effort`, `--codex-model`, and `--codex-effort`. Launching starts a durable tmux driver, not a background child of the laptop agent. Read its returned run directory and session name. Confirm `status.json` reaches `running`, `waiting_quota`, or an explained terminal state before reporting launch success. A tmux session alone is not proof the agents are working.

Return one complete attach command with the actual returned session name:

```bash
ssh -F ~/.ssh/config -t jhbuild@152.228.174.33 'tmux attach -t vps-<actual-run-name>'
```

There is no dashboard and no requirement for the user to watch. The terminal shows driver status; each status row names its full native event log. Long jobs and additional workers have their own tmux windows or sessions.

## Unattended decision policy

- Solve routine implementation issues and ordinary test failures without waiting for the user. Preserve the plan's decisions and the project's normal review, test and merge process.
- Record major changes to outcome/architecture, cost changes, and destructive operations absent from the plan on the relevant issue: evidence, attempted options, recommendation, affected tasks and what can continue. Park that decision and continue independent work. Use `gh-axi` where installed, otherwise `gh`; write comments through a body file. Posting these run-related issue updates is authorized by this skill's invocation.
- Record repeated failed attempts rather than cycling indefinitely. For a blocker affecting other features, first try an allowed stronger model or the other agent with the existing evidence. If still blocked, record it and continue other issues. Stop with `blocked` only when no independent task can progress.
- A worker's apparent success is evidence to inspect. Verify results and delivery before `done`. Distinguish a completed test process from passing assertions and a pushed branch from an approved merge.

## Durable supervision and workers

The helper is a narrow recovery driver, not another project workflow. It runs native Claude/Codex headless turns, checks `quota-axi` before inference, and enforces native subscription authentication. Fresh quota at zero keeps that provider idle. Both exhausted means a process sleep and quota recheck at most every 15 minutes, without model calls. Unknown quota is not treated as available. Authentication or CLI failures try the other usable provider; if neither is usable and no quota reset can help, `status.json` records the block.

Each turn receives the brief and latest `HANDOFF.md`, inspects the actual repo/jobs, and writes `control.json` at the end. Control states are `continue`, `wait` with seconds, `done`, and `blocked`. The helper clears old control before each turn and honors a completion only after a successful native turn. Current progress, attempts, pending decisions, worktrees and job identities belong in the handoff, not only in the conversation. A provider killed mid-turn may have uncheckpointed work: the successor must inspect git, processes and logs before retrying.

For extra workers, create their isolated worktrees and brief files, then call the same `start` helper with unique names and settings. They inherit the run's policy and concurrency limit; a worker creates further workers only when its brief authorizes that delegation. Track their run directories in the supervisor's handoff. The driver exposes `VPS_RUN_DRIVER` and `VPS_RUN_DIR` to each turn. Respect the agreed worker count and avoid making every worker a supervisor.

For multi-hour tests, use a dedicated tmux window running a quoted command script. That script writes its log and exit status to the run directory; the supervisor checkpoints the exact window/job and requests `wait` instead of spending tokens polling. Ending a native headless turn can reap its background shell children, so a shell `&` inside an agent tool is insufficient. Quota waits leave independent tmux jobs running. Do not restart an existing expensive job merely because its agent session ended.

## Inspect, stop and recover

Read `<run-directory>/status.json`, `HANDOFF.md`, and the named `turn-*.jsonl` log. Confirm actual process/session identity when status is stale. Raw logs can contain project output; keep them private and post only relevant, sanitized evidence to issues.

Create `<run-directory>/STOP` to prevent another turn at the next checkpoint/wake. This preserves existing tests and workers; an in-flight turn finishes first. To resume, remove that run's STOP file and run:

```bash
python3 ~/.agents/skills/vps-run/scripts/run.py resume <absolute-run-directory>
```

Run `resume` inside a named remote tmux window/session, not as an SSH child that dies on disconnect. A per-run lock refuses duplicate drivers. Resume uses the stored brief and handoff, preserving models and settings; adjust `config.json` only for an explicit steering request. After host reboot the files survive, but tmux jobs do not automatically restart: inspect exit artifacts and recover deliberately. Laptop disconnection alone does not stop them.

Use `tmux kill-session` only for a run the user asks to terminate, after identifying all its windows. It can terminate long tests. Never stop the pre-existing Firstmate crew or unrelated sessions.

## Verify changes to this skill

Run `python3 scripts/test_run.py` for offline fallback/checkpoint/reset checks. Run the skill-creator validator for the frontmatter. Check actual native CLI flags on the target host before changing the driver. Sources: [Codex noninteractive execution](https://developers.openai.com/codex/noninteractive), [Codex authentication](https://developers.openai.com/codex/auth), and [Claude programmatic execution](https://code.claude.com/docs/en/headless). Installed CLI help owns version-specific flags.
