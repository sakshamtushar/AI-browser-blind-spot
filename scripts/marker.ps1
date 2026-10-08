param([Parameter(Mandatory)][string]$Message)
try { New-EventLog -LogName Application -Source C0C0NLAB -ErrorAction SilentlyContinue } catch {}
Write-EventLog -LogName Application -Source C0C0NLAB -EventId 902 -EntryType Information -Message "C0C0N MARKER $Message"
"$(Get-Date -Format o) MARKER $Message" | Add-Content C:\lab\markers.log
