#!/usr/bin/env bash
# New-machine setup for Omarchy (Arch) and macOS. Safe to rerun. Keep it bash 3.2 compatible (macOS).
# Usage: ./bootstrap.sh [--link-only]
set -euo pipefail
c=$(cd "$(dirname "$0")" && pwd -P)

if [ "${1:-}" != "--link-only" ]; then
  case $(uname -s) in
    Linux)
      grep -vE '^[[:space:]]*(#|$)' "$c/packages.txt" | sudo pacman -S --needed -
      ;;
    Darwin)
      if ! command -v brew >/dev/null; then
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        eval "$(/usr/local/bin/brew shellenv)"
      fi
      brew bundle --file "$c/Brewfile"
      ;;
    *)
      echo "unsupported OS: $(uname -s)" >&2
      exit 1
      ;;
  esac

  if ! command -v mise >/dev/null; then
    curl -fsSL https://mise.run | sh
    PATH="$HOME/.local/bin:$PATH"
  fi
  mise install
fi

"$c/link.sh"

if [ "$(uname -s)" = Darwin ] && [ "${SHELL:-}" != /usr/local/bin/bash ]; then
  echo "One-time: make Homebrew bash your login shell:"
  echo "  echo /usr/local/bin/bash | sudo tee -a /etc/shells && chsh -s /usr/local/bin/bash"
fi
