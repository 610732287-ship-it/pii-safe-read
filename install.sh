#!/usr/bin/env bash
# pii-safe-read installer
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/610732287-ship-it/pii-safe-read/main/install.sh | bash
set -euo pipefail

BASE="${BASE_URL:-https://raw.githubusercontent.com/610732287-ship-it/pii-safe-read/main}"
SKILL_NAME="pii-safe-read"

# Detect target client: CodeBuddy vs WorkBuddy
if [ -n "${__CFBundleIdentifier:-}" ] && echo "${__CFBundleIdentifier}" | grep -qi "codebuddy"; then
  SKILLS_DIR="$HOME/.codebuddy/skills"
elif [ -n "${CODEBUDDY_CONFIG_DIR:-}" ]; then
  SKILLS_DIR="$CODEBUDDY_CONFIG_DIR/skills"
elif [ -n "${WORKBUDDY_CONFIG_DIR:-}" ]; then
  SKILLS_DIR="$WORKBUDDY_CONFIG_DIR/skills"
else
  SKILLS_DIR="$HOME/.workbuddy/skills"
fi

TARGET="$SKILLS_DIR/$SKILL_NAME"
mkdir -p "$TARGET/references" "$TARGET/scripts"

# NOTE: cd into the target dir and download with RELATIVE paths.
# On Windows Git Bash the curl on PATH may be a native exe that cannot
# write to MSYS-style absolute paths (fails with "curl: (23) ERROR on write").
# Relative paths work with both MSYS curl and native curl.exe.
cd "$TARGET"

for f in "SKILL.md" "references/pii_rules.json" "references/workflow.md" "scripts/gen_safe_list.py"; do
  curl -fsSL -o "$f" "$BASE/$f"
done

echo "Installed: $TARGET"
ls -1 "$TARGET" "$TARGET/references" "$TARGET/scripts"
