#!/usr/bin/env python3
"""analyze_profile.py <UserData dir> [--redact] — dump AI-relevant artifacts from a Chromium-family profile."""
import sys, os, json, gzip, base64, sqlite3, re, pathlib, datetime, argparse
from ccl_chromium_reader.storage_formats import ccl_leveldb
from ccl_chromium_reader import ccl_chromium_localstorage, ccl_chromium_indexeddb, ccl_chromium_sessionstorage
ap = argparse.ArgumentParser(); ap.add_argument('ud'); ap.add_argument('--redact', action='store_true'); ap.add_argument('--grep', default='C0C0N')
a = ap.parse_args(); UD = pathlib.Path(a.ud); D = UD / 'Default'
SECRET = re.compile(r'(\+?91[ -]?[0-9]{10}|[0-9]{10}|leosectrainings(@gmail\.com)?|sk-[A-Za-z0-9_-]{16,}|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{6,}|AIza[0-9A-Za-z_-]{30,})')
def red(s):
    s = str(s)
    return SECRET.sub(lambda m: m.group(0)[:10] + '…[REDACTED]', s) if a.redact else s
def wk(ts):  # webkit µs → iso
    try: return (datetime.datetime(1601,1,1) + datetime.timedelta(microseconds=int(ts))).isoformat()
    except: return str(ts)
print(f'# Profile analysis: {UD}')
# --- Local State ---
try:
    ls = json.load(open(UD/'Local State', encoding='utf-8'))
    print('\n## Local State'); print('top keys:', ', '.join(sorted(ls)))
    print('os_crypt:', {k: (v[:16]+'…' if isinstance(v,str) else v) for k,v in ls.get('os_crypt',{}).items()})
    for k in ('perplexity','brave','glic'):
        if k in ls:
            v = ls[k]; print(f'{k}:', ', '.join(sorted(v)) if isinstance(v, dict) else v)
            if k=='perplexity' and 'features' in v:
                f = json.loads(gzip.decompress(base64.b64decode(v['features'])))
                print(f'  perplexity.features: {len(f)} flags →', ', '.join(sorted(f))[:3000])
except Exception as e: print('Local State:', e)
piid = UD/'piid'
if piid.exists(): print('piid:', piid.read_text().strip())
# --- Preferences / Secure Preferences ---
for f in ('Secure Preferences','Preferences'):
    p = D/f
    if not p.exists(): continue
    d = json.load(open(p, encoding='utf-8'))
    ext = d.get('extensions',{}).get('settings',{})
    if ext:
        print(f'\n## {f}: extensions')
        for eid,e in ext.items():
            m=e.get('manifest',{}); print(f"- {eid} loc={e.get('location')} from_webstore={e.get('from_webstore')} {m.get('name')!r} v{m.get('version')} path={e.get('path')} first_install={wk(e.get('first_install_time')) if e.get('first_install_time') else ''}")
    def walk(o,path=''):
        if isinstance(o,dict):
            for k,v in o.items():
                kp=f'{path}.{k}' if path else k
                if re.search(r'perplexity|comet|sidecar|assistant|ai_chat|glic|gemini|copilot|dxt|mcp|agent', k, re.I): print('  PREF', kp, '=', red(json.dumps(v))[:200])
                walk(v,kp)
    print(f'\n## {f}: AI-related keys'); walk(d)
# --- History ---
h = D/'History'
if h.exists():
    con = sqlite3.connect(f'file:{h}?mode=ro&immutable=1', uri=True)
    print('\n## History (urls)')
    for r in con.execute('select u.url,u.title,u.visit_count,u.last_visit_time from urls u order by last_visit_time desc limit 40'):
        print(f'- {wk(r[3])}  {r[0]}  [{r[1]!r}] x{r[2]}')
    try:
        print('## History downloads:', con.execute('select count(*) from downloads').fetchone()[0])
    except: pass
# --- Local Extension Settings (all extensions) ---
les = D/'Local Extension Settings'
if les.exists():
    print('\n## Local Extension Settings (LevelDB, live + deleted records)')
    for ext in sorted(les.iterdir()):
        print(f'\n### {ext.name}')
        try:
            db = ccl_leveldb.RawLevelDb(ext)
            n=0
            for rec in db.iterate_records_raw():
                n+=1
                k = rec.user_key.decode('utf-8','replace'); v = rec.value.decode('utf-8','replace')
                print(f'  [{rec.state.name} seq={rec.seq}] {k} = {red(v)[:400]}')
            print(f'  ({n} records)')
            db.close()
        except Exception as e: print('  err', e)
# --- Local Storage ---
lsd = D/'Local Storage'/'leveldb'
if lsd.exists():
    print('\n## Local Storage')
    try:
        st = ccl_chromium_localstorage.LocalStoreDb(lsd)
        for host in st.iter_storage_keys():
            recs = list(st.iter_records_for_storage_key(host))
            print(f'- {host}: {len(recs)} records')
            for r in recs[:15]:
                print(f'    {r.script_key} = {red(r.value)[:200]!r}')
        st.close()
    except Exception as e: print('  err', e)
# --- IndexedDB ---
idb = D/'IndexedDB'
if idb.exists():
    print('\n## IndexedDB origins')
    for o in sorted(idb.iterdir()): print('-', o.name)
# --- grep canary across profile ---
print(f'\n## grep {a.grep!r} across profile files')
hits=0
for p in UD.rglob('*'):
    if p.is_file() and p.stat().st_size < 50_000_000:
        try:
            b = p.read_bytes()
            if a.grep.encode() in b or a.grep.encode('utf-16-le') in b:
                hits+=1; print('-', p.relative_to(UD))
        except: pass
print(f'({hits} files)')
