"""hva_script.py: Phase 3 'S' (script) actor runs. See RUNBOOK-phase3-human-vs-agent.md.

Drives Comet with Playwright (CDP) through task T1 on a COPY of the Comet profile:
open form-hva.html, fill name/email/notes programmatically, submit. One browser launch per run.
Appends one row per run to C:\\lab\\hva\\runs.csv (run_id,actor,task,start_utc,end_utc).

  python hva_script.py --user-data-dir C:\\lab\\hva\\comet-S\\User Data --runs 3 --gap 60
"""
import argparse, csv, datetime as dt, os, subprocess, time
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument('--exe', default=r'C:\Program Files\Perplexity\Comet\Application\comet.exe')
ap.add_argument('--user-data-dir', required=True)
ap.add_argument('--profile', default='Profile 1')
ap.add_argument('--runs', type=int, default=3)
ap.add_argument('--first', type=int, default=1, help='resume from this run number')
ap.add_argument('--gap', type=int, default=60)
ap.add_argument('--base', default='http://192.168.1.14:8088')
ap.add_argument('--log', default=r'C:\lab\hva\runs.csv')
a = ap.parse_args()

now = lambda: dt.datetime.now(dt.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
marker = lambda m: subprocess.run(['powershell', '-NoProfile', '-File', r'C:\lab\scripts\marker.ps1', '-Message', m], capture_output=True)
new = not os.path.exists(a.log)
with open(a.log, 'a', newline='') as f:
    w = csv.writer(f)
    if new:
        w.writerow(['run_id', 'actor', 'task', 'start_utc', 'end_utc'])
    with sync_playwright() as p:
        for n in range(a.first, a.runs + 1):
            rid = f'S-T1-{n}'
            canary = f'C0C0N-CANARY-HVA-S-T1-{n}'
            start = now(); marker(f'hva start {rid}')
            ctx = p.chromium.launch_persistent_context(
                a.user_data_dir, executable_path=a.exe, headless=False,
                args=['--start-maximized', '--no-first-run', '--no-default-browser-check', f'--profile-directory={a.profile}', '--remote-debugging-port=9222'],
                ignore_default_args=['--disable-extensions', '--enable-automation', '--disable-component-extensions-with-background-pages',
                                     '--disable-background-networking', '--disable-default-apps', '--disable-component-update'],
                no_viewport=True)  # real window size; an emulated viewport left Submit 'outside the viewport' on run 2
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto(f'{a.base}/form-hva.html', wait_until='load', timeout=30000)
            time.sleep(2)
            page.fill('input[name=name]', canary)
            page.fill('input[name=email]', f'hva-s-{n}@lab.local')
            page.fill('textarea[name=notes]', f'Phase 3 script run {n}')
            page.locator('button[type=submit]').scroll_into_view_if_needed()
            page.click('button[type=submit]')
            page.wait_for_load_state('load'); time.sleep(5)
            ctx.close(); time.sleep(3)
            end = now(); marker(f'hva end {rid}')
            w.writerow([rid, 'S', 'T1', start, end]); f.flush()
            print(rid, start, end, flush=True)
            if n < a.runs:
                time.sleep(a.gap)
