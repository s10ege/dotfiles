#!/usr/bin/env python3
"""Isolated two-laptop checks; no real home, remote, installs or reloads.
Run: python3 agents/skills/dotfiles-sync/test.py
Push checks execute the skill's Git protocol, not an agent approval conversation.
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
APPLY = Path(__file__).with_name('apply.sh')


def run(args, cwd, env, ok=True):
    result = subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True)
    if ok:
        assert result.returncode == 0, (args, result.stdout, result.stderr)
    return result


with tempfile.TemporaryDirectory(prefix='.dotfiles-sync-test-', dir=ROOT) as tmp:
    base = Path(tmp)
    env = dict(os.environ, HOME=str(base), GIT_CONFIG_GLOBAL='/dev/null',
               GIT_CONFIG_NOSYSTEM='1', GIT_AUTHOR_NAME='Test',
               GIT_AUTHOR_EMAIL='test@example.invalid', GIT_COMMITTER_NAME='Test',
               GIT_COMMITTER_EMAIL='test@example.invalid')
    bare = base / 'remote.git'
    run(['git', 'init', '--bare', '--initial-branch=main', str(bare)], base, env)
    a = base / 'A' / '.config'
    b = base / 'B' / '.config'
    for repo in (a, b):
        repo.parent.mkdir()
    run(['git', 'clone', str(bare), str(a)], base, env)
    for path in ('bash', 'nvim', 'mise', 'hypr', 'aerospace', 'agents/skills/dotfiles-sync'):
        (a / path).mkdir(parents=True)
    (a / 'bash/example').write_text('first\n' + 'context\n' * 20 + 'last\n')
    (a / 'nvim/lazy-lock.json').write_text('{}\n')
    (a / 'mise/config.toml').write_text('[tools]\n')
    (a / 'Brewfile').write_text('# Mac\n')
    (a / 'hypr/bindings.conf').write_text('# Linux\n')
    (a / 'aerospace/aerospace.toml').write_text('# Mac\n')
    (a / 'README.md').write_text('fixture\n')
    (a / 'link.sh').write_text('#!/bin/bash\nprintf "link\\n" >> "$CALLS"\n')
    shutil.copy2(APPLY, a / 'agents/skills/dotfiles-sync/apply.sh')
    run(['git', 'add', '--', 'bash', 'nvim', 'mise', 'Brewfile', 'hypr', 'aerospace',
         'agents', 'README.md', 'link.sh'], a, env)
    run(['git', 'commit', '-m', 'Fixture'], a, env)
    run(['git', 'push', '-u', 'origin', 'main'], a, env)
    run(['git', 'clone', str(bare), str(b)], base, env)
    shims = base / 'bin'
    shims.mkdir()
    for name in ('mise', 'brew', 'aerospace', 'hyprctl', 'uname', 'gitleaks'):
        shim = shims / name
        shim.write_text('''#!/bin/bash
name=${0##*/}
if [ "$name" = uname ]; then echo "$TEST_OS"; exit; fi
printf '%s' "$name" >> "$CALLS"
printf ' %s' "$@" >> "$CALLS"
printf '\\n' >> "$CALLS"
if [ "$name" = aerospace ] && [ "${FAIL_DRY_RUN:-}" = 1 ] && [ "${2:-}" = --dry-run ]; then exit 1; fi
if [ "$name" = gitleaks ] && [ "${FAIL_SCAN:-}" = 1 ]; then exit 1; fi
''')
        shim.chmod(0o755)
    calls = base / 'calls'
    env.update(PATH=str(shims) + ':' + env['PATH'], CALLS=str(calls), TEST_OS='Linux')

    def git(*args, repo=a, ok=True):
        return run(['git', *args], repo, env, ok)

    def publish(paths):
        if paths:
            git('add', '--', *paths)
        git('commit', '-m', 'Incoming fixture change')
        git('push')

    def apply(os_name='Linux', ok=True):
        calls.write_text('')
        target_env = dict(env, HOME=str(b.parent), TEST_OS=os_name)
        result = run(['bash', str(b / 'agents/skills/dotfiles-sync/apply.sh')], b,
                     target_env, ok)
        return calls.read_text().splitlines(), result

    # Initial unexplained index must stop before a commit or push.
    start = git('rev-parse', 'HEAD').stdout
    (a / 'README.md').write_text('unexplained\n')
    git('add', '--', 'README.md')
    assert git('diff', '--cached', '--quiet', ok=False).returncode == 1
    assert git('rev-parse', 'HEAD').stdout == start
    patch = git('diff', '--cached', '--binary').stdout
    patch_file = base / 'patch'
    patch_file.write_text(patch)
    git('apply', '--cached', '-R', str(patch_file))
    (a / 'README.md').write_text('fixture\n')

    # Approve only the first of two hunks, leaving same-file edits and noise.
    text = (a / 'bash/example').read_text().replace('first\n', 'approved\n').replace('last\n', 'skipped\n')
    (a / 'bash/example').write_text(text)
    (a / 'nvim/lazy-lock.json').write_text('{"noise":true}\n')
    diff = git('diff', '--binary', '--', 'bash/example').stdout
    parts = diff.split('@@')
    patch_file.write_text('@@'.join(parts[:3]))
    git('apply', '--cached', '--check', str(patch_file))
    git('apply', '--cached', str(patch_file))
    staged_tree = git('write-tree').stdout
    head = git('rev-parse', 'HEAD').stdout
    staged = git('show', ':bash/example').stdout
    assert staged.startswith('approved\n') and staged.endswith('last\n')
    assert git('diff', '--cached', '--name-only').stdout == 'bash/example\n'
    scan_env = dict(env, FAIL_SCAN='1')
    assert run(['gitleaks', 'git', '--staged', '--redact'], a, scan_env, False).returncode != 0
    assert git('rev-parse', 'HEAD').stdout == head
    run(['gitleaks', 'git', '--staged', '--redact'], a, env)
    assert git('write-tree').stdout == staged_tree and git('rev-parse', 'HEAD').stdout == head
    git('commit', '-m', 'Approve shell change')
    git('push')
    assert 'skipped' in git('diff', '--', 'bash/example').stdout
    assert git('diff', '--', 'nvim/lazy-lock.json').stdout
    assert apply()[0] == ['link']
    assert apply()[0] == []  # No-op repeat.

    # A reviewed untracked addition is staged by patch, not broad git add.
    (a / 'agents/new.md').write_text('approved new file\n')
    addition = git('diff', '--no-index', '--binary', '--', '/dev/null', 'agents/new.md', ok=False)
    assert addition.returncode == 1
    patch_file.write_text(addition.stdout)
    git('apply', '--cached', '--check', str(patch_file))
    git('apply', '--cached', str(patch_file))
    assert git('diff', '--cached', '--name-only').stdout == 'agents/new.md\n'
    run(['gitleaks', 'git', '--staged', '--redact'], a, env)
    git('commit', '-m', 'Approve new agent file')
    git('push')
    assert apply()[0] == ['link']

    (a / 'mise/config.toml').write_text('[tools]\nexample = "1"\n')
    publish(['mise/config.toml'])
    assert apply()[0] == ['mise install']

    (a / 'Brewfile').write_text('# changed Mac\n')
    (a / 'aerospace/aerospace.toml').write_text('# changed Mac\n')
    (a / 'hypr/bindings.conf').write_text('# changed Linux\n')
    publish(['Brewfile', 'aerospace/aerospace.toml', 'hypr/bindings.conf'])
    assert apply('Darwin')[0] == [f'brew bundle --file {b}/Brewfile --no-upgrade',
                                  'aerospace reload-config --dry-run', 'aerospace reload-config']
    (a / 'hypr/bindings.conf').write_text('# Linux reload\n')
    publish(['hypr/bindings.conf'])
    assert apply()[0] == ['hyprctl reload']

    # NUL parsing, deletion and cross-directory rename select both sides.
    newline = a / 'agents' / 'new\nfile.md'
    newline.write_text('new\n')
    publish(['agents/new\nfile.md'])
    assert apply()[0] == ['link']
    git('mv', '--', 'agents/new\nfile.md', 'hypr/renamed.md')
    publish([])
    assert apply()[0] == ['link', 'hyprctl reload']
    git('rm', '--', 'hypr/renamed.md')
    publish([])
    assert apply()[0] == ['hyprctl reload']

    # Dry-run failure prevents the real AeroSpace reload.
    (a / 'aerospace/aerospace.toml').write_text('# invalid fixture\n')
    publish(['aerospace/aerospace.toml'])
    env['FAIL_DRY_RUN'] = '1'
    observed, result = apply('Darwin', ok=False)
    assert result.returncode != 0 and observed == ['aerospace reload-config --dry-run']
    assert 'command failed' in result.stderr
    del env['FAIL_DRY_RUN']

    (b / 'README.md').write_text('local work\n')
    assert apply(ok=False)[1].returncode != 0
    (b / 'README.md').write_text('fixture\n')
    git('commit', '--allow-empty', '-m', 'Local divergence', repo=b)
    git('commit', '--allow-empty', '-m', 'Remote divergence')
    git('push')
    assert apply(ok=False)[1].returncode != 0  # Never merge divergent histories.

    # Exercise the real linker only in a fake home and copied repo on both OSes.
    for os_name in ('Linux', 'Darwin'):
        home = base / ('links-' + os_name)
        repo = home / '.config'
        for directory in ('agents/skills/dotfiles-sync', 'codex', 'opencode'):
            (repo / directory).mkdir(parents=True)
        shutil.copy2(ROOT / 'link.sh', repo / 'link.sh')
        (repo / 'codex/config.toml').write_text('[shared]\nenabled = true\n')
        (home / '.agents/skills/existing').mkdir(parents=True)
        (home / '.codex').mkdir()
        (home / '.codex/config.toml').write_text('[projects."/test"]\ntrust_level = "trusted"\n')
        link_env = dict(env, HOME=str(home), TEST_OS=os_name)
        run(['bash', str(repo / 'link.sh')], repo, link_env)
        for path in ('.agents/skills/dotfiles-sync', '.claude/skills/dotfiles-sync', '.codex/skills/dotfiles-sync'):
            assert (home / path).resolve() == repo / 'agents/skills/dotfiles-sync'
        assert (home / '.claude/skills/existing').resolve() == home / '.agents/skills/existing'
        assert 'trust_level' in (home / '.codex/config.toml').read_text()
        if os_name == 'Darwin':
            assert (home / '.bash_profile').is_symlink()
        run(['bash', str(repo / 'link.sh')], repo, link_env)  # Idempotent.
        shared = home / '.agents/skills/dotfiles-sync'
        shared.unlink()
        shared.mkdir()
        (shared / 'keep').write_text('existing real skill\n')
        result = run(['bash', str(repo / 'link.sh')], repo, link_env)
        assert 'real dir' in result.stdout and (shared / 'keep').is_file()

print('PASS: selected-hunk push protocol, staged/scan gates, two-clone apply, OS routing, failures and isolated linking')
