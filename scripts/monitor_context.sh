#!/bin/bash
# Estimate the size of files loaded into the AI assistant's context window (POSIX).
echo "=== Context file size estimate (bytes) ==="
find .agents .memory -type f -name "*.md" | xargs wc -c | sort -nr
[ -f "CLAUDE.md" ] && wc -c "CLAUDE.md"
[ -f "task.md" ] && wc -c "task.md"

echo "-----------------------------------"
TOTAL_BYTES=$(cat $(find .agents .memory -type f -name "*.md") CLAUDE.md task.md 2>/dev/null | wc -c)
echo "Total static context size: ~$((TOTAL_BYTES / 1024)) KB"
echo "Estimated tokens (1 token ~ 4 chars): ~$((TOTAL_BYTES / 4)) tokens"
