"""drive.py --exe <browser.exe> --user-data-dir <dir> --canary <TAG> [--urls u1 u2] [--form] [--wait 20] [--cdp-port N] [--keep-defaults]
Drives a Chromium-family browser through canary activity with Playwright, then closes it cleanly.
By default REMOVES Playwright's --disable-extensions/--enable-automation so bundled AI extensions stay active.
"""
import argparse, time, json, sys, datetime
from playwright.sync_api import sync_playwright
ap = argparse.ArgumentParser()
ap.add_argument('--exe', required=True); ap.add_argument('--user-data-dir', required=True); ap.add_argument('--canary', required=True)
ap.add_argument('--urls', nargs='*', default=[]); ap.add_argument('--form', action='store_true'); ap.add_argument('--wait', type=int, default=20)
ap.add_argument('--cdp-port', type=int, default=0); ap.add_argument('--keep-defaults', action='store_true'); ap.add_argument('--headless', action='store_true')
a = ap.parse_args()
base = 'http://192.168.1.14:8088'
urls = a.urls or [f'{base}/canary-{a.canary}-01.html', 'https://example.com/', f'{base}/form.html']
extra = ['--no-first-run', '--no-default-browser-check']
if a.cdp_port: extra.append(f'--remote-debugging-port={a.cdp_port}')
ignore = [] if a.keep_defaults else ['--disable-extensions', '--enable-automation', '--disable-component-extensions-with-background-pages', '--disable-background-networking', '--disable-default-apps', '--disable-component-update']
log = {'start': datetime.datetime.now().isoformat(), 'exe': a.exe, 'ud': a.user_data_dir, 'canary': a.canary, 'steps': []}
with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(a.user_data_dir, executable_path=a.exe, headless=a.headless, args=extra, ignore_default_args=ignore, viewport={'width': 1280, 'height': 800})
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    for u in urls:
        try:
            page.goto(u, wait_until='load', timeout=30000); time.sleep(3)
            log['steps'].append({'goto': u, 'title': page.title(), 'ua': page.evaluate('navigator.userAgent'), 'brands': page.evaluate('navigator.userAgentData ? navigator.userAgentData.brands : null')})
            if u.endswith('form.html') and a.form:
                page.fill('input[name=name]', f'C0C0N-CANARY-{a.canary}-FORM'); page.fill('input[name=email]', f'{a.canary.lower()}@lab.local'); page.fill('textarea[name=notes]', f'submitted by drive.py for {a.canary}')
                page.click('button[type=submit]'); page.wait_for_load_state('load'); time.sleep(2)
                log['steps'].append({'form_submitted': True, 'result': page.title()})
        except Exception as e:
            log['steps'].append({'goto': u, 'error': str(e)[:200]})
    time.sleep(a.wait)
    log['pages_open'] = [pg.url for pg in ctx.pages]
    ctx.close()
log['end'] = datetime.datetime.now().isoformat()
print(json.dumps(log, indent=1))
