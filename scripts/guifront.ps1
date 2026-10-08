param([Parameter(Mandatory)][string]$Exe, [string]$Arg='', [string]$ProcMatch='')
Add-Type @"
using System;using System.Runtime.InteropServices;
public class W{
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int n);
}
"@
try { (New-Object -ComObject Shell.Application).MinimizeAll() } catch {}
Start-Sleep 1
if ($Exe -eq 'explorer') { Start-Process explorer -ArgumentList $Arg }
else { Start-Process $Exe -ArgumentList (@('--new-window','--start-maximized') + ($Arg -split ' ')) }
Start-Sleep 9
if (-not $ProcMatch) { $ProcMatch = [IO.Path]::GetFileNameWithoutExtension($Exe) }
$p = Get-Process | Where-Object { $_.ProcessName -match $ProcMatch -and $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if ($p) { [W]::ShowWindow($p.MainWindowHandle,3) | Out-Null; [W]::SetForegroundWindow($p.MainWindowHandle) | Out-Null; "fg: $($p.ProcessName) '$($p.MainWindowTitle)'" }
else { "no window for $ProcMatch" }
