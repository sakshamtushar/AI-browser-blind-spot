# run_browser.ps1 -Exe <path> -Url <url> [-Seconds 90] [-Args '<extra>'] [-Headless]
param([Parameter(Mandatory)][string]$Exe, [string]$Url = 'about:blank', [int]$Seconds = 90, [string]$Args = '', [switch]$Headless)
$name = [IO.Path]::GetFileNameWithoutExtension($Exe)
$a = @()
if ($Headless) { $a += '--headless=new', '--disable-gpu' }
$a += '--no-first-run', '--no-default-browser-check'
if ($Args) { $a += $Args.Split(' ') }
$a += $Url
"launch: $Exe $($a -join ' ')"
$p = Start-Process -PassThru -FilePath $Exe -ArgumentList $a
Start-Sleep $Seconds
"procs after ${Seconds}s: " + (Get-Process $name -EA SilentlyContinue | Measure-Object).Count
Get-Process $name -EA SilentlyContinue | Stop-Process -Force
Start-Sleep 3
