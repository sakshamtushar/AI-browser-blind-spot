#!/usr/bin/env bash
# labssh.sh "<cmd>"  — run a cmd.exe command on win11-endpoint with connect retries.
for i in 1 2 3 4 5 6; do
  out=$(ssh -o ConnectTimeout=15 -o ServerAliveInterval=15 -o ServerAliveCountMax=8 win11-endpoint "$1" 2>&1); rc=$?
  if [ $rc -ne 255 ] && ! grep -q "timed out\|Connection closed\|banner exchange\|Connection refused" <<<"$out"; then printf '%s\n' "$out"; exit $rc; fi
  echo "[labssh] attempt $i failed (rc=$rc), retrying in 10s..." >&2; sleep 10
done
printf '%s\n' "$out"; exit 1
