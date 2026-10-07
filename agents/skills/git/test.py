#!/usr/bin/env python3
"""Run: python3 agents/skills/git/test.py
Executes literal hook/rules checks and the written skill protocol, not live agent discovery.
All Git operations and linker checks use a temporary HOME, repo and bare remote.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
GUARD = ROOT / 'claude/git-guard.sh'
RULES = ROOT / 'codex/rules/git-guard.rules'
CODEX = shutil.which('codex')
GITLEAKS = shutil.which('gitleaks')


def run(args, cwd, env, ok=True, stdin=None):
    result = subprocess.run(args, cwd=cwd, env=env, input=stdin,
                            text=True, capture_output=True)
    if ok:
        assert result.returncode == 0, (args, result.stdout, result.stderr)
    return result


with tempfile.TemporaryDirectory(prefix='.git-skill-test-', dir=ROOT) as tmp:
    base = Path(tmp)
    env = dict(os.environ, HOME=str(base), GIT_CONFIG_GLOBAL='/dev/null',
               GIT_CONFIG_NOSYSTEM='1', GIT_AUTHOR_NAME='Test',
               GIT_AUTHOR_EMAIL='test@example.invalid', GIT_COMMITTER_NAME='Test',
               GIT_COMMITTER_EMAIL='test@example.invalid')
    # Do not inherit worker-specific Git hooks/config into throwaway repos.
    for key in list(env):
        if key.startswith(('GIT_CONFIG_KEY_', 'GIT_CONFIG_VALUE_')) or key in (
                'GIT_CONFIG_COUNT', 'GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE'):
            del env[key]

    denies = [
        'git add -A', 'git add .', 'git add --all', 'git add -- .',
        'git add ./', 'git add -A.txt', 'git add -vA own.txt', 'git add own.txt .',
        'git stash', 'git stash list', 'git reset --hard',
        'git reset HEAD --hard', 'git checkout -- .', 'git checkout .',
        'git co -- .', 'git clean -fd',
        'git -C /tmp add -A', 'git -C/tmp add .', 'git -C "" add -A',
        'git --git-dir=/tmp/repo reset --hard',
        'git --work-tree /tmp -c color.ui=false checkout -- .',
        'git -C "directory with (parentheses)" clean -fd',
        'git --no-pager --literal-pathspecs add -A',
        'env GIT_CONFIG_GLOBAL=/dev/null git clean -fd',
        '/usr/bin/git stash pop', 'true && git add -A',
        'git status; git clean -fd', 'git status\ngit add .',
        'bash -c "git reset --hard"', 'echo $(git clean -fd)',
        'git add "weird;name" .',
    ]
    allows = [
        'git status --porcelain=v1 -z', 'git add own.txt',
        'git add -- "path with spaces"', 'git add -- -A.txt',
        'git apply --cached --check patch', 'git apply --cached patch',
        'git diff --cached --binary', 'git checkout -b task --',
        'git checkout -- own.txt', 'git reset --soft HEAD~1',
        'git -C /tmp status', 'git -c color.ui=false add own.txt',
        'git --git-dir /tmp/repo --work-tree=/tmp diff',
        'git log -10 --format=%s', 'git push no-mistakes',
        'echo harmless',
    ]
    for command in denies + allows:
        result = run(['bash', str(GUARD)], base, env, False,
                     json.dumps({'tool_input': {'command': command}}))
        assert result.returncode == (2 if command in denies else 0), (command, result)
    assert run(['bash', str(GUARD)], base, env, False, '{broken').returncode == 2

    if CODEX:
        for args, denied in [
            (['git', 'add', '-A'], True), (['git', 'add', '.'], True),
            (['git', 'add', '--all'], True), (['git', 'add', '--', '.'], True),
            (['git', 'stash', 'list'], True), (['git', 'reset', '--hard'], True),
            (['git', 'checkout', '--', '.'], True), (['git', 'clean', '-fd'], True),
            (['git', 'add', 'own.txt'], False),
            (['git', 'apply', '--cached', 'patch'], False),
            (['git', '-C', '/tmp', 'status'], False),
        ]:
            result = run([CODEX, 'execpolicy', 'check', '--rules', str(RULES), *args], base, env)
            decision = json.loads(result.stdout).get('decision')
            assert (decision == 'forbidden') == denied, (args, result.stdout)
    else:
        print('NOT VERIFIED: Codex execpolicy CLI unavailable')

    # Real linker in a fake home; existing default.rules must remain untouched.
    repo = base / '.config'
    for directory in ('agents/skills/git/agents', 'claude', 'codex/rules', 'opencode'):
        (repo / directory).mkdir(parents=True)
    for path in ('link.sh', 'claude/settings.json', 'claude/git-guard.sh',
                 'codex/config.toml', 'codex/rules/git-guard.rules',
                 'agents/skills/git/SKILL.md', 'agents/skills/git/agents/openai.yaml'):
        shutil.copy2(ROOT / path, repo / path)
    (base / '.codex/rules').mkdir(parents=True)
    approvals = base / '.codex/rules/default.rules'
    approvals.write_text('# machine approvals\n')
    run(['bash', str(repo / 'link.sh')], repo, env)
    assert approvals.read_text() == '# machine approvals\n'
    assert (base / '.codex/rules/git-guard.rules').resolve() == repo / 'codex/rules/git-guard.rules'
    assert (base / '.codex/skills/git').resolve() == repo / 'agents/skills/git'
    assert (base / '.claude/skills/git').resolve() == repo / 'agents/skills/git'
    settings = json.loads((base / '.claude/settings.json').read_text())
    assert settings['attribution'] is False
    hook = settings['hooks']['PreToolUse'][0]
    assert hook['matcher'] == 'Bash'
    command = hook['hooks'][0]['command']
    assert run(['bash', '-c', command], repo, env, False,
               json.dumps({'tool_input': {'command': 'git add -A'}})).returncode == 2

    bare, work = base / 'remote.git', base / 'work'
    run(['git', 'init', '--bare', '--initial-branch=main', str(bare)], base, env)
    run(['git', 'clone', str(bare), str(work)], base, env)

    def git(*args, ok=True):
        return run(['git', *args], work, env, ok)

    (work / 'mixed.txt').write_text('first\n' + 'context\n' * 20 + 'last\n')
    (work / 'foreign.txt').write_text('baseline\n')
    git('add', '--', 'mixed.txt', 'foreign.txt')
    git('commit', '-m', 'Fixture')
    git('push', '-u', 'origin', 'main')
    git('checkout', '-b', 'task', '--')
    initial = git('rev-parse', 'HEAD').stdout
    (work / 'mixed.txt').write_text('own\n' + 'context\n' * 20 + 'foreign\n')
    (work / 'foreign.txt').write_text('foreign staged\n')
    git('add', '--', 'foreign.txt')
    (work / 'untracked foreign.txt').write_text('untouched\n')
    inventory = git('status', '--porcelain=v1', '-z').stdout.split('\0')
    assert '?? untracked foreign.txt' in inventory
    patch = base / 'selected.patch'
    diff = git('diff', '--binary', '--', 'mixed.txt').stdout
    patch.write_text('@@'.join(diff.split('@@')[:3]))

    def commit_selected():
        # Reenact the written protocol, including refusal before any index mutation.
        if git('diff', '--cached', '--quiet', ok=False).returncode:
            return 'foreign index'
        head = git('rev-parse', 'HEAD').stdout
        git('apply', '--cached', '--check', str(patch))
        git('apply', '--cached', str(patch))
        tree = git('write-tree').stdout
        if not GITLEAKS:
            return 'missing scanner'
        scan = run([GITLEAKS, 'git', '--staged', '--redact'], work, env, False)
        if scan.returncode:
            assert scan.returncode == 1 and 'leaks found' in scan.stderr, scan.stderr
            return 'scan blocked'
        assert git('rev-parse', 'HEAD').stdout == head
        assert git('write-tree').stdout == tree
        git('commit', '-m', 'Own hunk')
        return 'committed'

    foreign_tree = git('write-tree').stdout
    assert commit_selected() == 'foreign index'
    assert git('write-tree').stdout == foreign_tree
    assert git('rev-parse', 'HEAD').stdout == initial
    # Only the fixture owner removes its own staged fixture, via inverse patch.
    undo = base / 'foreign.patch'
    undo.write_text(git('diff', '--cached', '--binary').stdout)
    git('apply', '--cached', '-R', str(undo))
    outcome = commit_selected()
    assert outcome == ('committed' if GITLEAKS else 'missing scanner')
    assert git('show', ':mixed.txt').stdout == 'own\n' + 'context\n' * 20 + 'last\n'
    assert 'foreign' in git('diff', '--', 'mixed.txt').stdout
    assert 'foreign staged' in git('diff', '--', 'foreign.txt').stdout
    assert (work / 'untracked foreign.txt').read_text() == 'untouched\n'
    if GITLEAKS:
        git('push', '-u', 'origin', 'task')  # Only the temporary local bare remote.
        assert git('rev-parse', 'origin/task').stdout == git('rev-parse', 'HEAD').stdout
        before = git('rev-parse', 'HEAD').stdout
        secret = work / 'secret.txt'
        # Synthetic credential assembled at runtime so the test source is scan-clean.
        secret.write_text('github_token = "' + 'ghp_' + 'aB3dE7fG9hJ2kL4mN6pQ8rS1tU5vW0xY3zA9b' + '"\n')
        addition = git('diff', '--no-index', '--binary', '--', '/dev/null', 'secret.txt', ok=False)
        assert addition.returncode == 1
        patch.write_text(addition.stdout)
        assert commit_selected() == 'scan blocked'
        assert git('rev-parse', 'HEAD').stdout == before
    else:
        print('NOT VERIFIED: real gitleaks hit; unavailable scanner stopped commit')

print('PASS: hook deny/allow table, Codex prefixes, isolated linking, foreign index refusal, exact own hunk, staged secret gate and local bare-remote delivery')
