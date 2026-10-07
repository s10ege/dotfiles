---
name: git
description: Safely commit, push, or open a pull request (PR), including whenever an agent is about to perform those operations. Review ownership, stage exact hunks, scan secrets, and route delivery.
---

For `~/.config` itself, **dotfiles-sync stays the review and sync flow**; use
these ownership, scan and delivery safeguards within that flow. Respect explicit
local-only delivery instructions: a commit request alone does not authorize a push.

1. Record HEAD and inventory `git status --porcelain=v1 -z`,
   `git diff --binary`, `git diff --cached --binary`, and
   `git ls-files --others --exclude-standard -z`. Handle NUL-delimited paths,
   including renames. Inspect only task-owned untracked files, without following
   external symlinks. Never print credentials. If the index already contains
   unexplained changes, **stop and ask whose they are**. Do not commit or unstage
   them. Resume only after ownership and disposition are explicit; require an
   empty index before staging this operation.
2. Save only your own reviewed changes as a patch, including selected hunks,
   additions, deletions, file modes and renames. For a new file, use
   `git diff --no-index --binary -- /dev/null <path>` (exit 1 means differences).
   Recheck HEAD, the empty index, and selected file contents against the reviewed
   snapshot. If anything changed, stop and re-review. Check and stage only that
   patch with `git apply --cached --check <patch>` then
   `git apply --cached <patch>`. Never stage a whole file containing foreign hunks.
3. Inspect `git diff --cached --binary` and ensure it is exactly the reviewed
   patch. Record the approved staged tree with `git write-tree`. Run
   `gitleaks git --staged --redact`; if the installed version lacks `git`, use
   `gitleaks protect --staged --redact`. Stop on findings, missing scanner, or scan
   errors; never bypass the scan. The user decides false positives; do not add
   ignores or suppressions yourself. After their decision, rerun the scan.
4. Read `git log -10 --format=%s` and follow this repo's recent message style.
   No agent co-author trailers or "Generated with" lines. Immediately before
   committing, recheck HEAD and the index against the reviewed HEAD and approved
   staged tree; if either changed, stop. Serialize staging through commit with
   other agents. Inspect the resulting commit and message. If nothing was
   selected, make no commit or push. Never rebase over another agent's changes.
5. Before delivery from the main/default branch, ask each time:
   **"branch + PR or push to main?"** Do not infer the answer from past deliveries.
   If branch + PR is chosen, move your commits onto a task branch before pushing;
   do not reset the shared main branch. Existing task branches use branch + PR.
6. Check `git remote`. If it lists `no-mistakes`, use the **no-mistakes** skill and
   `git push no-mistakes`; that pipeline owns the PR, so do not open one yourself.
   Otherwise push the task branch with `git push -u origin <branch>` and open the
   PR with `gh-axi` (follow repo templates and check for an existing PR first).
   An explicitly approved main delivery without no-mistakes uses
   `git push origin HEAD:<main-branch>` without a PR. Never force push. On failure,
   stop and report it. Do not set up no-mistakes in repos that lack it.

Claude's Bash guard denies all `git stash` forms, including `stash list`, plus
broad adds and destructive resets/checkouts/clean. It handles literal commands,
global Git flags and shell separators conservatively; it is not a shell sandbox
and cannot resolve dynamically constructed commands, aliases or arbitrary scripts.
Codex's tracked `git-guard.rules` covers literal forbidden prefixes; prefix rules
cannot skip arbitrary `-C`/`-c` arguments or reordered flags. Rules govern requests
outside the sandbox, not all execution. Never use these gaps to bypass the rules.
