#!/usr/bin/env bash
# shot.sh <name> — capture the VM console screen to screenshots/<name>.png
N="$1"; V='D:\Vmware workstation pro\vmrun.exe'; VMX='D:\VMs\windows 11\Windows 11 x64.vmx'
~/.claude/skills/thor-lab-ops/scripts/ssh-lab.sh windows-host "\"$V\" -T ws -gu thorh -gp ${LAB_PW:?set LAB_PW} -vp ${LAB_PW:?set LAB_PW} captureScreen \"$VMX\" C:\Users\<user>\c0c0n\\$N.png" >/dev/null 2>&1
scp -q "windows-host:C:/Users/<user>/c0c0n/$N.png" "$(dirname "$0")/../screenshots/$N.png" && echo "screenshots/$N.png"
