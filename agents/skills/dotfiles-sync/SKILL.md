---
name: dotfiles-sync
description: Explicitly review, commit and sync approved dotfiles changes between Omarchy and the Intel Mac, or pull and apply incoming changes.
disable-model-invocation: true
---

Work in `~/.config`; read its README layout rules. Invoke as `/dotfiles-sync`
(Claude) or `$dotfiles-sync` (Codex). Default to **push**; `apply` pulls on this
laptop. Never use `just sync`, `git add -A`, or `git add .`.

## Push

1. Record HEAD and inventory `git status --porcelain=v1 -z`,
   `git diff --binary`, `git diff --cached --binary`, and
   `git ls-files --others --exclude-standard -z`. Handle NUL-delimited paths,
   including renames. Inspect only allowlisted untracked files, without following
   external symlinks. Never print credentials or send them to a translation agent.
   If the index already contains unexplained changes, **stop and ask whose they
   are**. Do not commit or unstage them. Resume only after ownership and disposition
   are explicit; require an empty index before staging this operation.
2. Show **all** changes grouped by topic, with paths and a one-line explanation
   per group. Flag `nvim/lazy-lock.json`, Codex machine tables (projects, hook
   state, notices), and plugin-written Claude settings as tool noise, skipped by
   default. Distinguish intentional settings from noise within the same file.
   Get the user's explicit yes/no for each group; unanswered groups stay skipped.
3. Save the approved diff as a patch, including selected hunks, additions,
   deletions, file modes and renames. For a new file, use a patch from
   `git diff --no-index --binary -- /dev/null <path>` (exit 1 means differences).
   Recheck HEAD, the empty index, and approved file contents against the reviewed
   snapshot. If anything changed, stop and re-review. Check and stage only that
   patch with `git apply --cached --check <patch>` then
   `git apply --cached <patch>`. Never stage a whole file containing skipped hunks.
4. Inspect `git diff --cached --binary` and ensure it is exactly the approved
   patch. Run `gitleaks git --staged --redact`; if the installed version lacks
   `git`, use `gitleaks protect --staged --redact`. Stop on findings, missing
   scanner, or scan errors; never bypass the scan. Immediately before committing,
   recheck HEAD and the index against the reviewed HEAD and approved staged tree
   (`git write-tree`); if either changed, stop. Serialize staging through commit
   with other agents. Commit with a clear topic message, without a co-author.
   If nothing was approved, make no commit or push.
5. Prepare any translation below, review and commit it separately using the same
   approval, patch staging, scanner and snapshot checks. Then `git push` using the
   configured upstream, without force. If translation is declined or unavailable,
   still push the approved source commit and report pending translation. On push
   failure, stop and report it; never
   start remote apply before a successful push.
6. Read `~/.config/agents/local/peer` as data, never source/eval it. It must contain
   one nonempty line: an SSH alias or `user@tailscale-host` (letters, digits,
   dots, underscores, hyphens and one optional `@`; no whitespace or leading `-`).
   If absent, report peer setup is missing and suggest apply mode there next time.
   Otherwise run:
   `ssh -o ConnectTimeout=5 <peer> '$HOME/.config/agents/skills/dotfiles-sync/apply.sh'`.
   On failure, say the peer may be offline and apply mode should run there next
   time; include the error, since SSH or the remote apply itself may have failed.

## Translation (both directions)

When an approved Linux change has a Mac counterpart, or vice versa, delegate
that translation to one subagent. Give it the **approved diff**, source/target OS
(the Mac is Intel, Ventura 13.7.8), exact permitted target file paths, relevant
current target contents, and README layout rules. Request a minimal proposed
diff, a one-line explanation per change, validation evidence, and an unsupported
list. Return patch text without editing the working tree. It must not stage,
commit, push, connect to the peer, or propose changes outside those paths. If
subagents are unavailable, report that limitation and leave translation pending
instead of silently substituting a different workflow.

- Hypr bindings <-> `aerospace/aerospace.toml`: translate intent, using Option for
  SUPER; check existing keys and command semantics.
- `packages.txt` <-> `mise/config.toml` for shared CLIs, `Brewfile` for Mac-only
  apps. Verify upstream Intel Mac/Ventura and Linux compatibility before adding.
- New home-directory configs: update the appropriate OS branch in `link.sh`.
  XDG configs read in place need no link.

Review the returned diff yourself, then show it to the user for approval before
applying. Keep its commit separate from the source changes. List anything with
no equivalent as **unsupported**; never guess an equivalent or install packages
outside the manifests. Shared configs already work on both machines and need no
translation.

## Apply

Run `bash "$HOME/.config/agents/skills/dotfiles-sync/apply.sh"`. This records old
HEAD, pulls with `--ff-only`, reports `git diff --name-status OLD HEAD`, and runs
only the needed link/install/reload steps for this OS. Report what ran and any
failure; never run bootstrap or package cleanup. If a step fails after the pull,
the output identifies the failed command and old/new HEAD: fix the cause and
rerun that command explicitly, since another pull may have no incoming diff.
