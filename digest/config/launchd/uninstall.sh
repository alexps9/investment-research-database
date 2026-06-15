#!/bin/bash
# Uninstall HH Research launchd agents.

set -e

PLIST_DST="$HOME/Library/LaunchAgents"

for label in com.hh-research.daily-pipeline \
             com.hh-research.health-check \
             com.hh-research.broadcast; do
    launchctl unload "$PLIST_DST/${label}.plist" 2>/dev/null || true
    rm -f "$PLIST_DST/${label}.plist"
    echo "removed $label"
done

echo ""
echo "Uninstalled. State files in data/state/ are preserved."
