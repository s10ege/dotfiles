#!/usr/bin/env python3
"""Run native subscription agents in tmux, with disk handoffs and quota waits."""
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def quota_delay(provider, now=None):
    """None means unknown; zero means usable; otherwise seconds until reset."""
    if provider.get('state', {}).get('status') != 'fresh':
        return None
    windows = provider.get('windows', [])
    if not windows:
        return None
    exhausted = [w for w in windows if isinstance(w.get('percentRemaining'), (int, float))
                 and w['percentRemaining'] <= 0]
    if not exhausted:
        return 0 if all(isinstance(w.get('percentRemaining'), (int, float)) for w in windows) else None
    delays = []
    for window in exhausted:
        try:
            reset = datetime.fromisoformat(window['resetsAt'].replace('Z', '+00:00')).timestamp()
            delays.append(max(60, reset - (time.time() if now is None else now) + 30))
        except (KeyError, ValueError, TypeError):
            delays.append(900)
    return max(delays)


def limit_error(events):
    errors = [event for event in events if event.get('type') in ('error', 'turn.failed')
              or (event.get('type') == 'result' and event.get('is_error'))]
    return any(re.search(r'usage_limit|rate.limit|hit your limit|usage limit|quota exceeded|too many requests|\b429\b',
                         json.dumps(event), re.I) for event in errors)


def environment(run):
    env = os.environ.copy()
    for key in ('ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_BASE_URL',
                'CLAUDE_CODE_OAUTH_TOKEN', 'CLAUDE_CODE_USE_BEDROCK', 'CLAUDE_CODE_USE_VERTEX',
                'CLAUDE_CODE_USE_FOUNDRY', 'OPENAI_API_KEY', 'CODEX_API_KEY', 'OPENAI_BASE_URL',
                'OPENAI_API_BASE', 'CLAUDECODE'):
        env.pop(key, None)
    env['VPS_RUN_DIR'] = str(run)
    env['VPS_RUN_DRIVER'] = str(Path(__file__).resolve())
    return env


def command(provider, config):
    if provider == 'claude':
        args = ['claude', '-p', '--dangerously-skip-permissions', '--verbose',
                '--output-format', 'stream-json']
        if config.get('claude_effort'):
            args += ['--effort', config['claude_effort']]
    else:
        args = ['codex', 'exec', '--dangerously-bypass-approvals-and-sandbox', '--json',
                '-c', 'forced_login_method="chatgpt"', '-c', 'model_provider="openai"']
        if config.get('codex_effort'):
            args += ['-c', 'model_reasoning_effort=' + json.dumps(config['codex_effort'])]
    if config.get(provider + '_model'):
        args += ['--model', config[provider + '_model']]
    return args + ['-']


def subscription(provider, env):
    args = ['claude', 'auth', 'status'] if provider == 'claude' else ['codex', 'login', 'status']
    result = subprocess.run(args, env=env, capture_output=True, text=True, timeout=60)
    if provider == 'codex':
        return result.returncode == 0 and 'chatgpt' in (result.stdout + result.stderr).lower()
    try:
        auth = json.loads(result.stdout)
        return result.returncode == 0 and auth.get('loggedIn') and auth.get('authMethod') == 'claude.ai'
    except ValueError:
        return False


def prompt(run):
    handoff = run / 'HANDOFF.md'
    return f'''Execute the agreed brief below using this project's normal workflow and instructions.
You are an unattended VPS agent. Your durable run directory is {run}.
Read its HANDOFF.md, inspect git and existing workers/jobs before acting, and keep that handoff
current BEFORE long waits, dispatch, risky steps, and at each completed task. Include exact worktree,
branch, issue/PR, job session, log paths, attempted fixes, verification, and pending decisions.
Another Claude or Codex agent may take over without this conversation. Preserve their work.
Handle routine fixes yourself. Record major plan/cost changes and unplanned destructive operations
on the relevant issue, park that decision, and continue independent tasks. Record repeated failures;
for blockers affecting other work, try a stronger allowed model before parking them.
Launch every helper agent in bypass-permissions mode, in its own worktree. Follow the brief's
concurrency limits. Use native subscription logins only; preserve disabled paid overflow.
Run multi-hour commands in their own named tmux windows with logs and exit status files so they
survive this turn ending, provider exhaustion, and SSH disconnection. Check existing job identity
before starting or retrying. Wait without inference: checkpoint and request a timed wait below.
At the END of a successful turn write {run / 'control.json'} with JSON:
{{"state":"continue","summary":"next actionable work"}}; or
{{"state":"wait","seconds":900,"summary":"which existing job/condition to recheck"}}; or
{{"state":"done","summary":"verified outcomes and delivery links"}}; or
{{"state":"blocked","summary":"all remaining work needs a recorded human decision"}}.
Use done only after the brief's completion and delivery checks pass. Use blocked only when no
independent work can continue. Write HANDOFF.md before control.json. Do not modify config.json,
status.json, the driver, or its lock. A previous control.json is cleared before each turn.

BRIEF:
{(run / 'brief.md').read_text()}

LATEST HANDOFF:
{handoff.read_text() if handoff.exists() else 'First turn. Inspect current state before starting.'}
'''


def resume(run):
    with (run / 'lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            return drive(run)
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
            save(run / 'status.json', {'state': 'blocked', 'summary': str(error)})
            raise


def drive(run):
    config = json.loads((run / 'config.json').read_text())
    env = environment(run)
    providers = [config.get('first', 'claude')]
    providers.append('codex' if providers[0] == 'claude' else 'claude')
    failed = {}
    cooldown = {}

    def status(state, **details):
        value = dict(state=state, pid=os.getpid(), updated_at=datetime.now(timezone.utc).isoformat(), **details)
        save(run / 'status.json', value)
        print(json.dumps(value), flush=True)

    while True:
        if (run / 'STOP').exists():
            status('stopped', summary='STOP requested; existing jobs are preserved')
            return 0
        quota = subprocess.run(['quota-axi', '--provider', 'claude,codex', '--json'],
                               env=env, capture_output=True, text=True, timeout=90, check=True)
        readings = {p['provider']: p for p in json.loads(quota.stdout)['providers']}
        delays = {p: quota_delay(readings.get(p, {})) for p in providers if p not in failed}
        for provider, delay in delays.items():
            if delay is not None:
                delays[provider] = max(delay, cooldown.get(provider, 0) - time.time())
        ready = next((p for p in providers if delays.get(p) == 0 and p not in failed), None)
        if ready is None:
            waits = [d for d in delays.values() if d is not None and d > 0]
            if not waits:
                status('blocked', summary='No verified subscription quota is available', errors=failed)
                return 1
            delay = min(min(waits), 900)
            status('waiting_quota', seconds=delay, errors=failed)
            time.sleep(delay)
            continue
        if not subscription(ready, env):
            failed[ready] = 'Native subscription login required'
            continue
        control = run / 'control.json'
        control.unlink(missing_ok=True)
        log = run / ('turn-' + str(time.time_ns()) + '.jsonl')
        status('running', provider=ready, log=str(log))
        with log.open('w') as output:
            result = subprocess.run(command(ready, config), input=prompt(run), text=True,
                                    cwd=config['cwd'], env=env, stdout=output, stderr=subprocess.STDOUT)
        events = []
        with log.open(errors='replace') as recorded:
            for line in recorded:
                try:
                    event = json.loads(line)
                    if isinstance(event, dict) and event.get('type') in ('result', 'error', 'turn.failed', 'turn.completed'):
                        events.append(event)
                except ValueError:
                    pass
        if limit_error(events):
            providers = list(reversed(providers))
            # Vendor reads can lag a rejected turn. Avoid retrying it in a tight loop.
            cooldown[ready] = time.time() + 900
            continue
        completed = any(e.get('type') == 'turn.completed' if ready == 'codex' else
                        e.get('type') == 'result' and not e.get('is_error', True) for e in events)
        if result.returncode or not completed or any(e.get('type') == 'turn.failed' or
                (e.get('type') == 'result' and e.get('is_error')) for e in events):
            failed[ready] = f'CLI failed; inspect {log}'
            continue
        if not control.exists():
            status('blocked', provider=ready, summary=f'Missing end-of-turn checkpoint; inspect {log}')
            return 1
        directive = json.loads(control.read_text())
        state = directive['state']
        if state not in ('done', 'blocked', 'wait', 'continue'):
            raise ValueError('Unknown control state: ' + str(state))
        status(state, provider=ready, summary=directive.get('summary', ''))
        if state in ('done', 'blocked'):
            return 0 if state == 'done' else 1
        failed.clear()
        if state == 'wait':
            time.sleep(max(30, min(3600, float(directive.get('seconds', 900)))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    start = commands.add_parser('start', help='Create a named detached tmux run')
    start.add_argument('--name', required=True)
    start.add_argument('--cwd', type=Path, required=True)
    start.add_argument('--brief', type=Path, required=True)
    start.add_argument('--first', choices=('claude', 'codex'), default='claude')
    for provider in ('claude', 'codex'):
        start.add_argument('--' + provider + '-model')
        start.add_argument('--' + provider + '-effort')
    again = commands.add_parser('resume', help='Run/restart a saved driver in the foreground')
    again.add_argument('run', type=Path)
    args = parser.parse_args()
    if args.action == 'resume':
        return resume(args.run.resolve())
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,39}', args.name):
        parser.error('name must contain 1-40 letters, digits, underscores or hyphens')
    cwd, brief = args.cwd.resolve(strict=True), args.brief.resolve(strict=True)
    session = 'vps-' + args.name
    run = Path.home() / '.local/state/vps-run' / args.name
    run.mkdir(parents=True, exist_ok=False)
    (run / 'brief.md').write_text(brief.read_text())
    config = {k: v for k, v in vars(args).items() if k not in ('action', 'brief', 'cwd', 'name')}
    config['cwd'] = str(cwd)
    save(run / 'config.json', config)
    shell = shlex.join([sys.executable, str(Path(__file__).resolve()), 'resume', str(run)])
    shell += '; echo ' + shlex.quote('Driver exited. See status.json and turn logs in ' + str(run)) + '; exec /bin/bash'
    subprocess.run(['tmux', 'new-session', '-d', '-s', session, '-c', str(cwd), shell], check=True)
    print(json.dumps({'run': str(run), 'session': session, 'attach': 'tmux attach -t ' + session}))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f'vps-run: {error}', file=sys.stderr)
        sys.exit(1)
