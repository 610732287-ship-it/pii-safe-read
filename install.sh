#!/usr/bin/env bash
# pii-safe-read installer
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/USERNAME/REPO/main/install.sh | bash
set -euo pipefail

BASE="${BASE_URL:-https://raw.githubusercontent.com/USERNAME/REPO/main}"
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

for f in "SKILL.md" "references/pii_rules.json" "references/workflow.md" "scripts/gen_safe_list.py"; do
  curl -fsSL -o "$TARGET/$f" "$BASE/$f"
done

echo "Installed: $TARGET"
ls -1 "$TARGET" "$TARGET/references" "$TARGET/scripts"
