<#
.SYNOPSIS
  c0c0n AI-browser lab collector. Snapshots endpoint state into C:\lab\collect\<ts>-<label>\.
.PARAMETER Label      short tag, e.g. 00-baseline, 10-comet-installed, 21-claude-after-chat
.PARAMETER Profiles   optional browser profile roots to copy via VSS (live DBs), e.g.
                      "$env:LOCALAPPDATA\Perplexity\Comet\User Data","$env:LOCALAPPDATA\Google\Chrome\User Data"
.PARAMETER NoFs       skip the (slow) recursive filesystem listing
.NOTES
  Run elevated. Writes an Application-log marker (source C0C0NLAB, id 900) so Elastic windows are unambiguous.
#>
param(
  [Parameter(Mandatory)][string]$Label,
  [string[]]$Profiles = @(),
  [switch]$NoFs
)
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
$ts  = Get-Date -Format 'yyyyMMdd-HHmmss'
$out = "C:\lab\collect\$ts-$Label"
New-Item -ItemType Directory -Force -Path $out | Out-Null
function Log($m){ $line = "$(Get-Date -Format 'HH:mm:ss') $m"; $line | Tee-Object -FilePath "$out\collect.log" -Append }

# --- marker for Elastic ---
try { New-EventLog -LogName Application -Source C0C0NLAB -ErrorAction SilentlyContinue } catch {}
Write-EventLog -LogName Application -Source C0C0NLAB -EventId 900 -EntryType Information -Message "C0C0N MARKER collect-start label=$Label ts=$ts"
Log "collect start label=$Label -> $out"

# --- system summary ---
@{
  label=$Label; ts=$ts; host=$env:COMPUTERNAME; user=$env:USERNAME
  os=(Get-CimInstance Win32_OperatingSystem).Version; bootUtc=(Get-CimInstance Win32_OperatingSystem).LastBootUpTime.ToUniversalTime().ToString('o')
  nowUtc=(Get-Date).ToUniversalTime().ToString('o')
} | ConvertTo-Json | Set-Content "$out\summary.json"

# --- filesystem listings ---
if (-not $NoFs) {
  $roots = @($env:LOCALAPPDATA, $env:APPDATA, $env:ProgramData, "$env:USERPROFILE\Downloads", "$env:USERPROFILE\Desktop",
            'C:\Program Files', 'C:\Program Files (x86)', 'C:\Windows\Prefetch', 'C:\Windows\Tasks', 'C:\Windows\System32\Tasks', 'C:\Windows\Temp')
  foreach ($r in $roots) {
    if (-not (Test-Path $r)) { continue }
    $name = ($r -replace '[:\\ ()]', '_').Trim('_')
    Log "fs listing $r"
    Get-ChildItem -LiteralPath $r -Recurse -Force -ErrorAction SilentlyContinue |
      Where-Object { $_.FullName -notlike 'C:\lab\*' } |
      Select-Object FullName, Length, @{n='IsDir';e={$_.PSIsContainer}},
        @{n='CreatedUtc';e={$_.CreationTimeUtc.ToString('o')}}, @{n='ModifiedUtc';e={$_.LastWriteTimeUtc.ToString('o')}} |
      Export-Csv -NoTypeInformation -Encoding UTF8 "$out\fs-$name.csv"
  }
}

# --- registry ---
$regDir = "$out\registry"; New-Item -ItemType Directory -Force -Path $regDir | Out-Null
$keys = @(
  'HKCU\Software',
  'HKLM\SOFTWARE\Policies',
  'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
  'HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall',
  'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths',
  'HKLM\SOFTWARE\Clients', 'HKLM\SOFTWARE\RegisteredApplications',
  'HKLM\SOFTWARE\Google', 'HKLM\SOFTWARE\WOW6432Node\Google',
  'HKLM\SOFTWARE\Microsoft\Edge', 'HKLM\SOFTWARE\WOW6432Node\Microsoft\Edge',
  'HKLM\SOFTWARE\Perplexity', 'HKLM\SOFTWARE\WOW6432Node\Perplexity', 'HKLM\SOFTWARE\Comet',
  'HKLM\SOFTWARE\BraveSoftware', 'HKLM\SOFTWARE\WOW6432Node\BraveSoftware',
  'HKLM\SOFTWARE\Mozilla', 'HKLM\SOFTWARE\Chromium',
  'HKLM\SYSTEM\CurrentControlSet\Services',
  'HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\TaskCache\Tree',
  'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\FileExts',
  'HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32',
  'HKCU\Software\Microsoft\Windows\CurrentVersion\Search\RecentApps'
)
foreach ($k in $keys) {
  $f = "$regDir\" + ($k -replace '[\\ ]', '_') + '.reg'
  & reg.exe export $k $f /y 2>&1 | Out-Null
  if (-not (Test-Path $f)) { "MISSING $k" | Add-Content "$regDir\_missing.txt" }
}
# installed apps as CSV (both hives + per-user)
Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*','HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue |
  Select-Object PSChildName, DisplayName, DisplayVersion, Publisher, InstallDate, InstallLocation, UninstallString, @{n='Hive';e={$_.PSPath -replace '.*::',''}} |
  Export-Csv -NoTypeInformation -Encoding UTF8 "$out\installed-apps.csv"
Get-AppxPackage -AllUsers -ErrorAction SilentlyContinue | Select-Object Name, PackageFullName, InstallLocation, Version | Export-Csv -NoTypeInformation -Encoding UTF8 "$out\appx-packages.csv"

# --- execution artifacts ---
$exDir = "$out\execution"; New-Item -ItemType Directory -Force -Path $exDir | Out-Null
New-Item -ItemType Directory -Force -Path "$exDir\Prefetch" | Out-Null
Get-ChildItem 'C:\Windows\Prefetch\*.pf' -ErrorAction SilentlyContinue | ForEach-Object { Copy-Item $_.FullName "$exDir\Prefetch\" -Force -ErrorAction SilentlyContinue }
foreach ($pair in @(@('C:\Windows\appcompat\Programs\Amcache.hve','Amcache.hve'), @('C:\Windows\System32\sru\SRUDB.dat','SRUDB.dat'),
                    @("$env:LOCALAPPDATA\Microsoft\Windows\WebCache\WebCacheV01.dat",'WebCacheV01.dat'))) {
  $src,$dst = $pair
  if (Test-Path $src) { Log "esentutl vss copy $src"; & esentutl.exe /y $src /vss /d "$exDir\$dst" 2>&1 | Out-Null }
}
& reg.exe save 'HKLM\SYSTEM' "$exDir\SYSTEM.hive" /y 2>&1 | Out-Null
& reg.exe save 'HKLM\SOFTWARE' "$exDir\SOFTWARE.hive" /y 2>&1 | Out-Null
& reg.exe save 'HKCU' "$exDir\NTUSER.hive" /y 2>&1 | Out-Null
& esentutl.exe /y "$env:LOCALAPPDATA\Microsoft\Windows\UsrClass.dat" /vss /d "$exDir\UsrClass.dat" 2>&1 | Out-Null

# --- live state ---
$live = "$out\live"; New-Item -ItemType Directory -Force -Path $live | Out-Null
Get-CimInstance Win32_Process | Select-Object ProcessId, ParentProcessId, Name, ExecutablePath, CommandLine, @{n='CreationUtc';e={$_.CreationDate.ToUniversalTime().ToString('o')}} |
  Export-Csv -NoTypeInformation -Encoding UTF8 "$live\processes.csv"
Get-Service | Select-Object Name, DisplayName, Status, StartType | Export-Csv -NoTypeInformation -Encoding UTF8 "$live\services.csv"
& schtasks.exe /query /v /fo CSV 2>$null | Set-Content "$live\scheduled-tasks.csv"
Get-NetTCPConnection -ErrorAction SilentlyContinue | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State, OwningProcess | Export-Csv -NoTypeInformation -Encoding UTF8 "$live\tcp.csv"
& netstat.exe -ano 2>$null | Set-Content "$live\netstat.txt"
Get-ChildItem Env: | Select-Object Name, Value | Export-Csv -NoTypeInformation -Encoding UTF8 "$live\env.csv"
Get-ChildItem "$env:ProgramData\Microsoft\Windows\Start Menu\Programs","$env:APPDATA\Microsoft\Windows\Start Menu\Programs" -Recurse -Filter *.lnk -ErrorAction SilentlyContinue | Select-Object FullName, LastWriteTimeUtc | Export-Csv -NoTypeInformation -Encoding UTF8 "$live\startmenu-lnk.csv"
& driverquery.exe /v /fo csv 2>$null | Set-Content "$live\drivers.csv"

# --- native messaging hosts + extension inventories (cheap, always) ---
$nm = "$out\native-messaging"; New-Item -ItemType Directory -Force -Path $nm | Out-Null
foreach ($hk in 'HKCU','HKLM') { foreach ($v in 'Google\Chrome','Microsoft\Edge','Chromium','BraveSoftware\Brave','Perplexity\Comet','Mozilla') {
  $k = "$hk\Software\$v\NativeMessagingHosts"; $f = "$nm\" + ($k -replace '[\\ ]','_') + '.reg'; & reg.exe export $k $f /y 2>&1 | Out-Null } }
Get-ChildItem -Path $nm -Filter *.reg | ForEach-Object {
  Select-String -Path $_.FullName -Pattern '@="(.+\.json)"' | ForEach-Object { $p = $_.Matches[0].Groups[1].Value -replace '\\\\','\'; if (Test-Path $p) { Copy-Item $p $nm -Force } }
}

# --- browser profiles via VSS (live DBs, WAL, LevelDB .log) ---
$Profiles = @($Profiles | ForEach-Object { $_ -split '[,;]' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
if ($Profiles.Count -gt 0) {
  $pDir = "$out\profiles"; New-Item -ItemType Directory -Force -Path $pDir | Out-Null
  Log "creating VSS shadow of C:"
  $res = (Get-WmiObject -List Win32_ShadowCopy).Create('C:\', 'ClientAccessible')
  $sc  = Get-WmiObject Win32_ShadowCopy | Where-Object { $_.ID -eq $res.ShadowID }
  if ($sc) {
    $link = 'C:\lab\vss'
    if (Test-Path $link) { & cmd.exe /c rmdir $link | Out-Null }
    & cmd.exe /c mklink /d $link ($sc.DeviceObject + '\') | Out-Null
    foreach ($p in $Profiles) {
      if (-not (Test-Path $p)) { Log "profile missing: $p"; continue }
      $rel = $p.Substring(3)  # strip C:\
      $dst = Join-Path $pDir (($p -replace '^C:\\','' -replace '[\\ ]','_'))
      Log "robocopy profile $p -> $dst"
      & robocopy.exe (Join-Path $link $rel) $dst /E /COPY:DAT /R:1 /W:1 /NFL /NDL /NJH /NJS /XD 'Cache' 'Code Cache' 'GPUCache' 'DawnCache' 'GrShaderCache' 'ShaderCache' 'GraphiteDawnCache' 'DawnGraphiteCache' 'DawnWebGPUCache' 'OptGuideOnDeviceModel' 'component_crx_cache' 'WidevineCdm' 2>&1 | Out-Null
    }
    & cmd.exe /c rmdir $link | Out-Null
    $sc.Delete() | Out-Null
    Log "VSS shadow deleted"
  } else { Log "VSS shadow creation FAILED" }
}

# --- manifest ---
Get-ChildItem $out -Recurse -File | Where-Object { $_.Name -ne 'manifest.csv' } |
  ForEach-Object { [pscustomobject]@{ Path=$_.FullName.Substring($out.Length+1); Size=$_.Length; SHA256=(Get-FileHash $_.FullName -Algorithm SHA256).Hash } } |
  Export-Csv -NoTypeInformation -Encoding UTF8 "$out\manifest.csv"
Write-EventLog -LogName Application -Source C0C0NLAB -EventId 901 -EntryType Information -Message "C0C0N MARKER collect-end label=$Label ts=$ts"
Log "collect done"
Write-Output $out
