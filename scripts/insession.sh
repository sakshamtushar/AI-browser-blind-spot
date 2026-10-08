#!/usr/bin/env bash
# insession.sh "<windows command line>" [timeout_s] — run inside thorh's interactive desktop via vmrun runProgramInGuest -interactive; prints output.
CMD="$1"; TO="${2:-600}"; TAG="c0c0n-$(date +%s)"; TMP=$(mktemp)
printf '@echo off\r\ncd /d C:\\lab\r\n( %s ) > C:\\lab\\run\\%s.log 2>&1\r\necho EXIT=%%ERRORLEVEL%% >> C:\\lab\\run\\%s.log\r\necho DONE > C:\\lab\\run\\%s.done\r\n' "$CMD" "$TAG" "$TAG" "$TAG" > "$TMP"
scp -q "$TMP" "win11-endpoint:C:/lab/run/$TAG.cmd"; rm -f "$TMP"
~/.claude/skills/thor-lab-ops/scripts/ssh-lab.sh windows-host "\"D:\\Vmware workstation pro\\vmrun.exe\" -T ws -vp ${LAB_PW:?set LAB_PW} -gu thorh -gp ${LAB_PW:?set LAB_PW} runProgramInGuest \"D:\VMs\windows 11\Windows 11 x64.vmx\" -interactive -nowait C:\Windows\System32\cmd.exe /c C:\lab\run\\$TAG.cmd" 2>&1 | grep -v "^#" | grep -v '^$'
t=0; while [ $t -lt $TO ]; do
  if ssh -o ConnectTimeout=15 win11-endpoint "if exist C:\lab\run\\$TAG.done echo DONE" 2>/dev/null | grep -q DONE; then break; fi
  sleep 5; t=$((t+5))
done
ssh -o ConnectTimeout=15 win11-endpoint "type C:\lab\run\\$TAG.log 2>nul & del C:\lab\run\\$TAG.cmd C:\lab\run\\$TAG.done 2>nul"
