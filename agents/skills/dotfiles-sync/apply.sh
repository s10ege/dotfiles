#!/usr/bin/env bash
# Pull dotfiles and apply only incoming paths. Compatible with macOS bash 3.2.
set -euo pipefail
export PATH="$HOME/.local/share/mise/shims:$HOME/.local/bin:/usr/local/bin:$PATH"
cd "$HOME/.config"
if [ -n "$(git status --porcelain=v1)" ]; then
  echo 'dotfiles-sync: checkout has local changes; review them before apply.' >&2
  exit 1
fi
old=$(git rev-parse HEAD)
git pull --ff-only
new=$(git rev-parse HEAD)
printf 'dotfiles-sync: %s -> %s\n' "$old" "$new"
git diff --name-status "$old" "$new"
paths=$(mktemp)
trap 'rm -f "$paths"' EXIT
# Treat renames as deletion + addition so both paths select their needed actions.
git diff --no-renames --name-only -z "$old" "$new" > "$paths"
link=false
mise=false
brew=false
aerospace=false
hypr=false
while IFS= read -r -d '' path; do
  case "$path" in
    link.sh|bash/*|agents/*|claude/*|codex/*|no-mistakes/*) link=true ;;
  esac
  case "$path" in
    mise/config.toml) mise=true ;;
    Brewfile) brew=true ;;
    aerospace/*) aerospace=true ;;
    hypr/*) hypr=true ;;
  esac
done < "$paths"
run() {
  printf 'Running:'
  printf ' %q' "$@"
  printf '\n'
  if "$@"; then
    printf 'Completed: %s\n' "$1"
  else
    echo "dotfiles-sync: command failed; fix and rerun it (incoming range $old..$new)." >&2
    exit 1
  fi
}
ran=false
if "$link"; then run bash "$HOME/.config/link.sh"; ran=true; fi
if "$mise"; then run mise install; ran=true; fi
case $(uname -s) in
  Darwin)
    if "$brew"; then run brew bundle --file "$HOME/.config/Brewfile" --no-upgrade; ran=true; fi
    if "$aerospace"; then
      run aerospace reload-config --dry-run
      run aerospace reload-config
      ran=true
    fi
    ;;
  Linux)
    if "$hypr"; then run hyprctl reload; ran=true; fi
    ;;
esac
if ! "$ran"; then echo 'dotfiles-sync: no install/link/reload steps needed.'; fi
