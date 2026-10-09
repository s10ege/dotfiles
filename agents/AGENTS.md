# Global agent instructions

Shared by Claude Code, Codex, opencode and Pi. Source of truth: `~/.config/agents/AGENTS.md` (symlinked into each agent).

## Writing and commits

- Never use the em dash "—". Use plain dash "-" instead.
- Never add agent co-author trailers or "Generated with" lines to commits.
- Never manually modify CHANGELOG.md files or any files that are marked as auto-generated.
- When writing skills, AGENTS.md or CLAUDE.md, use the `writing-for-agents` skill instead of `superpowers:writing-skills`.

## Engineering bar

- When making technical decisions, do not give much weight to development cost.
  Instead, prefer quality, simplicity, robustness, scalability, and long term maintainability.
- Minimum code that solves the problem. No features, abstractions, or configurability beyond what was asked. If 200 lines could be 50, rewrite it.
- For one-off or infrequent operational work, start with the simplest direct end-to-end path. Do not build wrappers, control planes, policy layers, custom verifiers, or automation unless the direct path exposes a concrete blocker or repeated need that justifies the added machinery.
- Keep diffs surgical: every changed line should trace to the request. Match existing style; do not reformat, restyle, or refactor adjacent code that works.
- Real defects are the exception: if you see lint errors, failing or flaky tests, or UI that clearly looks off, fix them even if you did not cause them, and keep that fix in its own commit. When end-to-end testing a product, be picky about the UI and aim for pixel perfection.
- Clean up only your own orphans (imports, variables, functions your change made unused). Mention pre-existing dead code instead of deleting it.

## Process

- State assumptions. If a request has several readings or something is unclear, ask instead of picking silently. Push back when a simpler approach exists.
- Turn tasks into verifiable goals (a test, a command, an observable result) and loop until verified.
- When doing bug fixes, always start with reproducing the bug in an E2E setting as closely aligned with how an end user would experience it as possible.
  This makes sure you find the real problem so your fix will actually solve it.
- Before using "dynamic workflows", "ultra code", Superpowers subagent execution, or any harness feature that immediately spawns a large swarm of subagents, always explain the tradeoffs and ask the user for explicit approval.
- Start every subagent or helper agent you spawn in bypass-permissions mode (Claude Code `mode: "bypassPermissions"` / `--dangerously-skip-permissions`, Codex `--dangerously-bypass-approvals-and-sandbox`), not manual or auto approval.

## Running alongside other agents

The user runs Claude Code and Codex at the same time, often on the same repo.

- Use the [git skill](skills/git/SKILL.md) whenever you commit, push or open a PR; for `~/.config` itself, dotfiles-sync stays the flow.
- Never run `git add -A`, `git add .`, `git stash`, `git reset --hard`, `git checkout -- .`, `git clean`, or a rebase that would touch changes you did not make.
- For parallel work on one repo, use a separate git worktree per agent (`herdr worktree ...`) instead of sharing a working tree.
- Do not edit shared agent config (`~/.config/agents`, `~/.claude/settings.json`, `~/.codex/config.toml`) unless asked; the dotfiles repo in `~/.config` owns it.

## Machines: Omarchy (Arch + Hyprland) and an Intel Mac (macOS 13), herdr

- Dotfiles live in `~/.config` (git repo `s10ege/dotfiles`) on both; see `~/.config/README.md`. Shared CLI tools come from mise on both. Shared skills live in `~/.agents/skills` and are linked into each agent with `~/.config/link.sh`.

## Web research

- Search DuckDuckGo: `curl -s -A 'Mozilla/5.0' 'https://html.duckduckgo.com/html/?q=<query>'` (result links are the `uddg=` targets). Read pages with `curl`, `gh` or `r.jina.ai/<url>`. Leave the Firecrawl MCP tools unused; their credits belong to project code.

## Browser automation (Omarchy)

- For agent browsing, scraping or browser tests use `scraper-chromium` (dedicated profile, fixed debug port 9223, no approval prompts). It prints the CDP websocket URL: `export CHROME_DEVTOOLS_AXI_BROWSER_URL="$(scraper-chromium)"`.
- Its window is pinned to workspace 5 silently by a Hyprland rule; never launch another Chromium, never use or touch the user's own Chromium or tabs, open tabs with `newpage --background`, and close tabs you are done with.

## Maintaining this file

Keep this file for knowledge useful to almost every future agent session.
Do not repeat what the codebase already shows; point to the authoritative file or command instead.
Prefer rewriting or pruning existing entries over appending new ones.
When updating this file, preserve this bar for all agents and keep entries concise.
