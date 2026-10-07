#!/usr/bin/env bash
# Bash 3.2 launcher; Python (shared mise tool) parses JSON and shell words, never evals.
# Conservative literal-command guard, not a shell interpreter. All stash forms denied.
python3 -c '
import json
import os
import shlex
import sys


def forbidden(words):
    # Git global options with separate values; attached and = forms skip below.
    valued = {"-C", "-c", "--git-dir", "--work-tree", "--namespace",
              "--config-env", "--exec-path", "--super-prefix"}
    i = 0
    while i < len(words) and words[i].startswith("-"):
        option = words[i]
        i += 2 if option in valued else 1
    if i >= len(words):
        return False
    command, args = words[i], words[i + 1:]
    options = args[:args.index("--")] if "--" in args else args
    paths = args[args.index("--") + 1:] if "--" in args else args
    broad = any(p.rstrip("/") in ("", ".", ":", ":(top)") for p in paths)
    if command in ("stash", "clean"):
        return True
    if command == "add":
        return broad or any(a == "--all" or
                            (a.startswith("-") and not a.startswith("--") and "A" in a)
                            for a in options)
    if command == "reset":
        return any(a.split("=", 1)[0] == "--hard" for a in options)
    if command in ("checkout", "co"):
        return broad
    return False


def blocked(command):
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()<>\n")
    lexer.whitespace = " \t\r"  # Keep newlines as command boundaries.
    words = list(lexer)
    for i, word in enumerate(words):
        if os.path.basename(word) == "git":
            end = i + 1
            while end < len(words) and not (words[end] and all(c in ";&|()<>\n" for c in words[end])):
                end += 1
            if forbidden(words[i + 1:end]):
                return True
        # Includes literal bash -c/eval commands. Quoted prose may also be denied.
        elif "git" in word and any(c.isspace() for c in word):
            if blocked(word):
                return True
    return False


try:
    command = json.load(sys.stdin)["tool_input"]["command"]
    if not isinstance(command, str):
        raise ValueError("command must be a string")
    denied = blocked(command)
except (ValueError, KeyError, TypeError):
    print("Git guard could not parse this Bash request; use a simple literal command.", file=sys.stderr)
    sys.exit(2)
if denied:
    print("Blocked by Git guard: use the git skill and stage only your own exact patch; destructive Git commands and all stash forms are forbidden.", file=sys.stderr)
    sys.exit(2)
' || exit 2
