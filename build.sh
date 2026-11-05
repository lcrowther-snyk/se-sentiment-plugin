#!/usr/bin/env bash
# Build the team .plugin with the real config.json (kept out of git).
# Usage: ./build.sh            -> dist/se-sentiment.plugin
set -euo pipefail
cd "$(dirname "$0")"
CFG=skills/update-se-sentiment/config.json
[ -f "$CFG" ] || { echo "Missing $CFG. Copy config.example.json to config.json and add the webhook_url."; exit 1; }
grep -q '"webhook_url": "https://hooks.slack.com/triggers/' "$CFG" || { echo "$CFG has no webhook_url."; exit 1; }
if git ls-files --error-unmatch "$CFG" >/dev/null 2>&1; then echo "ERROR: $CFG is tracked by git. Remove it from the repo first."; exit 1; fi
mkdir -p dist
rm -f dist/se-sentiment.plugin
zip -qr dist/se-sentiment.plugin .claude-plugin skills README.md -x '*.DS_Store' -x '*/__pycache__/*' -x '*/config.example.json'
echo "Built dist/se-sentiment.plugin (includes the webhook; share it only inside Snyk)."
