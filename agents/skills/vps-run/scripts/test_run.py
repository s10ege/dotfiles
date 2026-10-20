"""Offline contract checks for provider fallback and durable completion."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('run.py')


class RunnerTests(unittest.TestCase):
    def test_fallback_preserves_checkpoint_and_finishes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bindir = root / 'bin'
            bindir.mkdir()
            run = root / 'run'
            run.mkdir()
            (run / 'brief.md').write_text('Run the agreed checks.')
            (run / 'config.json').write_text(json.dumps({'cwd': tmp, 'first': 'claude'}))
            quota = {'providers': [
                {'provider': 'claude', 'state': {'status': 'fresh'},
                 'windows': [{'percentRemaining': 0, 'resetsAt': '2099-01-01T00:00:00Z'}]},
                {'provider': 'codex', 'state': {'status': 'fresh'},
                 'windows': [{'percentRemaining': 50}]},
            ]}
            (bindir / 'quota-axi').write_text('#!/usr/bin/env python3\nprint(' + repr(json.dumps(quota)) + ')\n')
            (bindir / 'claude').write_text('#!/bin/sh\necho "Claude must not run at zero quota" >&2\nexit 99\n')
            (bindir / 'codex').write_text('''#!/usr/bin/env python3
import json, os, pathlib, sys
if 'status' in sys.argv:
    print('Logged in using ChatGPT')
    sys.exit(0)
assert '--dangerously-bypass-approvals-and-sandbox' in sys.argv
assert 'forced_login_method="chatgpt"' in sys.argv
assert 'OPENAI_API_KEY' not in os.environ
assert 'ANTHROPIC_API_KEY' not in os.environ
assert 'already completed' in sys.stdin.read()
r = pathlib.Path(os.environ['VPS_RUN_DIR'])
(r / 'HANDOFF.md').write_text('Verified result in result.txt')
(r / 'control.json').write_text(json.dumps({'state': 'done', 'summary': 'Checks passed'}))
print(json.dumps({'type': 'turn.completed'}))
''')
            (run / 'HANDOFF.md').write_text('A previous agent already completed setup.')
            for path in bindir.iterdir():
                path.chmod(0o755)
            env = dict(os.environ, PATH=str(bindir) + os.pathsep + os.environ['PATH'],
                       OPENAI_API_KEY='must-be-removed', ANTHROPIC_API_KEY='must-be-removed')
            result = subprocess.run(['python3', str(SCRIPT), 'resume', str(run)], env=env,
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            status = json.loads((run / 'status.json').read_text())
            self.assertEqual(status['state'], 'done')
            self.assertEqual(status['provider'], 'codex')
            self.assertTrue(list(run.glob('turn-*.jsonl')))

    def test_rate_limit_cooldown_does_not_disable_provider_forever(self):
        spec = importlib.util.spec_from_file_location('vps_run', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            (run / 'brief.md').write_text('Finish the checks.')
            (run / 'config.json').write_text(json.dumps({'cwd': tmp, 'first': 'claude'}))
            available = {'state': {'status': 'fresh'}, 'windows': [{'percentRemaining': 50}]}
            clock = [1000]
            launches = []
            def execute(args, **kwargs):
                if args[0] == 'quota-axi':
                    quota = {'providers': [dict(provider='claude', **available),
                                           dict(provider='codex', state={'status': 'fresh'}, windows=[{'percentRemaining': 0}])]}
                    return subprocess.CompletedProcess(args, 0, json.dumps(quota), '')
                if 'status' in args:
                    reply = json.dumps({'loggedIn': True, 'authMethod': 'claude.ai'}) if args[0] == 'claude' else 'Logged in using ChatGPT'
                    return subprocess.CompletedProcess(args, 0, reply, '')
                launches.append(args[0])
                if len(launches) <= 1:
                    kwargs['stdout'].write(json.dumps({'type': 'error', 'message': 'usage_limit exceeded'}) + '\n')
                    return subprocess.CompletedProcess(args, 1)
                (run / 'control.json').write_text(json.dumps({'state': 'done'}))
                kwargs['stdout'].write(json.dumps({'type': 'turn.completed'} if args[0] == 'codex' else {'type': 'result', 'is_error': False}) + '\n')
                return subprocess.CompletedProcess(args, 0)
            sleeps = []
            def sleep(seconds):
                sleeps.append(seconds)
                self.assertLess(len(sleeps), 3, 'Quota reset did not re-enable Claude')
                clock[0] += seconds
            with patch.object(module.subprocess, 'run', execute), patch.object(module.time, 'sleep', sleep), patch.object(module.time, 'time', lambda: clock[0]):
                self.assertEqual(module.resume(run), 0)
            self.assertEqual(len(launches), 2)
            self.assertGreaterEqual(clock[0], 1900)

    def test_failed_native_turn_cannot_claim_completion(self):
        spec = importlib.util.spec_from_file_location('vps_run', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            (run / 'brief.md').write_text('Run checks.')
            (run / 'config.json').write_text(json.dumps({'cwd': tmp, 'first': 'codex'}))
            def execute(args, **kwargs):
                if args[0] == 'quota-axi':
                    quota = {'providers': [{'provider': 'codex', 'state': {'status': 'fresh'},
                                            'windows': [{'percentRemaining': 50}]}]}
                    return subprocess.CompletedProcess(args, 0, json.dumps(quota), '')
                if 'status' in args:
                    return subprocess.CompletedProcess(args, 0, 'Logged in using ChatGPT', '')
                (run / 'control.json').write_text(json.dumps({'state': 'done'}))
                kwargs['stdout'].write(json.dumps({'type': 'turn.failed', 'error': {'message': 'connection lost'}}) + '\n')
                return subprocess.CompletedProcess(args, 0)
            with patch.object(module.subprocess, 'run', execute):
                self.assertEqual(module.resume(run), 1)
            self.assertEqual(json.loads((run / 'status.json').read_text())['state'], 'blocked')

    def test_quota_and_terminal_errors_are_distinct(self):
        spec = importlib.util.spec_from_file_location('vps_run', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.quota_delay({'state': {'status': 'fresh'}, 'windows': [
            {'percentRemaining': 0, 'resetsAt': '2030-01-01T00:10:00Z'}]}, now=1893456000), 630)
        self.assertIsNone(module.quota_delay({'state': {'status': 'unavailable'}, 'windows': []}))
        self.assertEqual(module.quota_delay({'state': {'status': 'fresh'}, 'windows': [
            {'percentRemaining': 40}]}), 0)
        self.assertTrue(module.limit_error([{'type': 'result', 'is_error': True,
                                             'result': "You've hit your limit"}]))
        self.assertFalse(module.limit_error([{'type': 'assistant', 'message': 'Test rate limit errors'}]))
        self.assertFalse(module.limit_error([{'type': 'result', 'is_error': False,
                                              'result': 'Fixed rate limit handling'}]))


if __name__ == '__main__':
    unittest.main()
