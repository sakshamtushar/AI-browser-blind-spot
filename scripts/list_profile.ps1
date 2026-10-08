param([Parameter(Mandatory)][string]$UserData)
"UserData: $UserData exists=$(Test-Path $UserData)"
if (-not (Test-Path $UserData)) { exit }
'--- root ---'; (Get-ChildItem $UserData -Force -EA SilentlyContinue | Select-Object -Expand Name) -join ', '
'--- Default ---'; (Get-ChildItem "$UserData\Default" -Force -EA SilentlyContinue | Select-Object -Expand Name) -join ', '
'--- Default\Extensions ---'; Get-ChildItem "$UserData\Default\Extensions" -EA SilentlyContinue | ForEach-Object { $_.Name + ' -> ' + ((Get-ChildItem $_.FullName | Select-Object -Expand Name) -join ',') }
'--- Local Extension Settings ---'; (Get-ChildItem "$UserData\Default\Local Extension Settings" -EA SilentlyContinue | Select-Object -Expand Name) -join ', '
'--- IndexedDB ---'; (Get-ChildItem "$UserData\Default\IndexedDB" -EA SilentlyContinue | Select-Object -Expand Name) -join ', '
'--- Local State os_crypt ---'; try { $ls = Get-Content "$UserData\Local State" -Raw | ConvertFrom-Json; $ls.os_crypt.PSObject.Properties | ForEach-Object { $_.Name + ' = ' + ($_.Value.ToString().Substring(0, [Math]::Min(24, $_.Value.ToString().Length))) + '...' } } catch { "no Local State: $_" }
'--- size ---'; '{0:N1} MB' -f ((Get-ChildItem $UserData -Recurse -Force -EA SilentlyContinue | Measure-Object Length -Sum).Sum / 1MB)
