#!/bin/sh
# Hunt 06 (macOS): ChatGPT Atlas updater left behind after Atlas was removed
# Atlas shut down on 9 Aug 2026, but deleting the app leaves its LaunchAgent in place.
# Observed on a lab Mac: com.openai.atlas.update-helper.plist with no Atlas.app.
# Read-only. Run per user (or loop over /Users/*/Library/LaunchAgents).
agent=$(ls "$HOME/Library/LaunchAgents" 2>/dev/null | grep -i 'atlas')
app=$(ls /Applications "$HOME/Applications" 2>/dev/null | grep -i 'atlas')
if [ -n "$agent" ] && [ -z "$app" ]; then
  echo "ORPHANED: $agent (no Atlas app installed)"
elif [ -n "$agent" ]; then
  echo "Atlas installed: $app / $agent"
else
  echo "no Atlas LaunchAgent"
fi
