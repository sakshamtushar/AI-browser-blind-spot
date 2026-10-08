# hva_guide.ps1: guided console for the Phase 3 person (P) and agent (A) runs on thorhq-windows.
# Walks through 6 runs in alternating order, writes start/end markers, and appends each run to
# C:\lab\hva\runs.csv (UTC). Safe to close and reopen: finished runs are skipped.
$ErrorActionPreference = 'Stop'
$csv  = 'C:\lab\hva\runs.csv'
# Hostname, not the IP: Comet 153's assistant refuses private-IP URLs (seen 2026-10-07 on A-T1-1).
$form = 'http://thorhq-windows:8088/form-hva.html'
$notes = 'C:\lab\hva\notes.txt'
# 2026-10-07: switched to Chrome + Claude in Chrome (CP = person in Chrome, CA = Claude agent in Chrome).
# P-T1-1 (Comet, person) stays recorded from the first session.
$runs = 'CP-T1-1','CA-T1-1','CP-T1-2','CA-T1-2','CP-T1-3','CA-T1-3'
if (-not (Test-Path $csv)) { 'run_id,actor,task,start_utc,end_utc' | Set-Content -Encoding ascii $csv }
$done = @(Import-Csv $csv | ForEach-Object { $_.run_id })
function Utc { (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ") }
function Mark($m) { & powershell -NoProfile -File C:\lab\scripts\marker.ps1 -Message $m | Out-Null }

Write-Host "`nPhase 3: you vs Claude in Chrome, form task. $($runs.Count) runs, alternating." -ForegroundColor Cyan
Write-Host "Rules: use GOOGLE CHROME (not Comet). Open it from the Start menu or taskbar every time. Close Chrome fully at the end of each run.`n"
foreach ($r in $runs) {
  if ($done -contains $r) { Write-Host "  $r already recorded, skipping"; continue }
  $actor, $task, $n = $r.Split('-')
  $canary = "C0C0N-CANARY-HVA-$actor-$task-$n"
  Write-Host "`n==================== RUN $r ====================" -ForegroundColor Yellow
  if ($actor -like '*P') {
    Write-Host "YOU fill the form by hand. Type everything on the keyboard; no paste, no VMware 'type clipboard'."
    Write-Host "Press Enter below to START first, THEN open Chrome." -ForegroundColor Magenta
    Write-Host "  1. Open Chrome. Click the address bar, type:  $form  and press Enter."
    Write-Host "  2. Click Name and type:   $canary"
    Write-Host "  3. Email: hva-p-$n@lab.local    Notes: anything short"
    Write-Host "  4. Click 'Submit request', wait for 'Request received', then close Chrome."
  } else {
    $prompt = "Open $form and fill the form: name $canary, email hva-a-$n@lab.local, notes 'Phase 3 agent run $n'. Then submit it."
    Set-Clipboard -Value $prompt
    Write-Host "CLAUDE IN CHROME fills the form. Do not touch the page yourself."
    Write-Host "  1. Open Chrome. Click the Claude icon in the toolbar to open its side panel (do not type a URL yourself)."
    Write-Host "  2. Paste the prompt (already on your clipboard) and send it:"
    Write-Host "     $prompt" -ForegroundColor Green
    Write-Host "  3. When Claude asks to act on thorhq-windows, choose 'Allow this time' (not Always). When it says the form is submitted, close Chrome."
    Write-Host "Press Enter below to START first, THEN open Chrome." -ForegroundColor Magenta
    Write-Host "  If it refuses again: open the form yourself (type the URL), then in the assistant ask:" -ForegroundColor DarkYellow
    Write-Host "  'Fill in this form: name $canary, email hva-a-$n@lab.local, notes Phase 3 agent run $n. Then submit it.'" -ForegroundColor DarkYellow
    Write-Host "  and answer the note question with: fallback" -ForegroundColor DarkYellow
  }
  Read-Host "Press Enter to START $r (then do the steps)"
  $start = Utc; Mark "hva start $r"
  Read-Host "Press Enter when $r is finished and Chrome is closed"
  $end = Utc; Mark "hva end $r"
  "$r,$actor,$task,$start,$end" | Add-Content -Encoding ascii $csv
  $note = Read-Host "Anything unusual about $r? (Enter = nothing)"
  if ($note) { "$r | $(Utc) | $note" | Add-Content -Encoding ascii $notes }
  Write-Host "Recorded $r  ($start -> $end)" -ForegroundColor Green
  if ($r -ne $runs[-1]) {
    Write-Host "Waiting 2 minutes so runs don't overlap in the logs..."
    for ($s = 120; $s -gt 0; $s -= 10) { Write-Host -NoNewline "$s "; Start-Sleep 10 }
    Write-Host ""
  }
}
Write-Host "`nAll runs recorded in $csv. Tell Claude 'runs done' to collect and analyse." -ForegroundColor Cyan
Read-Host "Press Enter to close"
