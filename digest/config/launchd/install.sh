#!/bin/bash
# One-shot installer for HH Research launchd automation.
# Run from the repo root: bash config/launchd/install.sh
#
# Installs three launchd agents:
#   00:00  com.hh-research.daily-pipeline      run daily pipeline + publish to personal wiki
#   00:30  com.hh-research.health-check        verify pipeline at least started
#   09:30  com.hh-research.broadcast           send card to enterprise group webhook

set -e

REPO_DIR="/Users/haolinguo/claude code/HH research/daily-digest"
PLIST_SRC="$REPO_DIR/config/launchd"
PLIST_DST="$HOME/Library/LaunchAgents"

cd "$REPO_DIR"

echo "==> Making scripts executable..."
chmod +x scripts/run_daily_pipeline.sh \
         scripts/health_check.sh \
         scripts/broadcast_today.sh

echo "==> Creating data directories..."
mkdir -p data/state data/logs/cron

echo "==> Copying plist files to $PLIST_DST ..."
mkdir -p "$PLIST_DST"
for plist in com.hh-research.daily-pipeline.plist \
             com.hh-research.health-check.plist \
             com.hh-research.broadcast.plist; do
    cp "$PLIST_SRC/$plist" "$PLIST_DST/$plist"
    echo "    copied $plist"
done

echo "==> Unloading any previous instances (ignore 'No such process')..."
for label in com.hh-research.daily-pipeline \
             com.hh-research.health-check \
             com.hh-research.broadcast; do
    launchctl unload "$PLIST_DST/${label}.plist" 2>/dev/null || true
done

echo "==> Loading agents..."
for label in com.hh-research.daily-pipeline \
             com.hh-research.health-check \
             com.hh-research.broadcast; do
    launchctl load "$PLIST_DST/${label}.plist"
    echo "    loaded $label"
done

echo ""
echo "==> Installed. Verify with:"
echo "    launchctl list | grep hh-research"
echo ""
echo "==> Manual trigger (anytime, for testing):"
echo "    launchctl start com.hh-research.daily-pipeline"
echo "    launchctl start com.hh-research.health-check"
echo "    launchctl start com.hh-research.broadcast"
echo ""
echo "==> Uninstall later with:"
echo "    bash config/launchd/uninstall.sh"
