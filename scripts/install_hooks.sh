#!/usr/bin/env bash
# Install the DueDateLab git hooks into .git/hooks/.
# Run this once per clone, or after updating the hook source.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
hook_src="${repo_root}/scripts/pre-commit"
hook_dst="${repo_root}/.git/hooks/pre-commit"

if [[ ! -f "${hook_src}" ]]; then
  echo "hook source missing: ${hook_src}" >&2
  exit 1
fi

install -m 0755 "${hook_src}" "${hook_dst}"
echo "installed: ${hook_dst}"
