#!/usr/bin/env python3
"""diff_collections.py <before_dir> <after_dir> [-o report.md] [--filter substr]
Compares two collect.ps1 bundles (unzipped): filesystem listings, installed apps, services,
scheduled tasks, processes, Prefetch, native-messaging manifests, and .reg exports.
"""
import argparse, csv, glob, io, os, re, sys
from collections import defaultdict

def read_csv(path):
    if not os.path.exists(path): return []
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def fs_index(d):
    idx = {}
    for p in glob.glob(os.path.join(d, 'fs-*.csv')):
        for r in read_csv(p):
            idx[r['FullName']] = r
    return idx

def reg_index(d):
    """Return {file: {key: set(value lines)}} from .reg exports (UTF-16)."""
    out = {}
    for p in glob.glob(os.path.join(d, 'registry', '*.reg')) + glob.glob(os.path.join(d, 'native-messaging', '*.reg')):
        try: txt = open(p, encoding='utf-16').read()
        except Exception:
            try: txt = open(p, encoding='utf-8', errors='replace').read()
            except Exception: continue
        keys = defaultdict(set); cur = None
        for line in txt.splitlines():
            if line.startswith('[') and line.endswith(']'): cur = line[1:-1]; keys[cur]  # ensure key exists
            elif cur and line.strip(): keys[cur].add(line.strip())
        out[os.path.basename(p)] = keys
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('before'); ap.add_argument('after')
    ap.add_argument('-o', '--out'); ap.add_argument('--filter', default='', help='only show paths/keys containing this (case-insensitive)')
    ap.add_argument('--max', type=int, default=400)
    a = ap.parse_args(); flt = a.filter.lower()
    W = io.StringIO()
    def P(s=''): W.write(s + '\n')
    P(f'# Delta: `{os.path.basename(a.before)}` → `{os.path.basename(a.after)}`')
    # --- filesystem ---
    b, f = fs_index(a.before), fs_index(a.after)
    added = [p for p in f if p not in b]; removed = [p for p in b if p not in f]
    modified = [p for p in f if p in b and (f[p]['ModifiedUtc'] != b[p]['ModifiedUtc'] or f[p]['Length'] != b[p]['Length']) and f[p]['IsDir'] != 'True']
    def show(title, items):
        items = [p for p in items if flt in p.lower()]
        P(f'\n## {title} ({len(items)})')
        # collapse: show top-level dirs with counts, then files up to max
        tops = defaultdict(int)
        for p in items:
            m = re.match(r'(C:\\(?:Users\\[^\\]+\\AppData\\(?:Local|Roaming)\\[^\\]+|Program Files(?: \(x86\))?\\[^\\]+|ProgramData\\[^\\]+|Windows\\[^\\]+)\\?[^\\]*)', p)
            tops[m.group(1) if m else p[:60]] += 1
        for k, n in sorted(tops.items(), key=lambda x: -x[1])[:40]: P(f'- `{k}` … {n}')
        if len(items) <= a.max:
            P(); [P(f'    {p}' + (f"  ({f[p]['Length']} B)" if p in f and f[p]['Length'] else '')) for p in sorted(items)]
    show('Files/dirs added', added); show('Files removed', removed); show('Files modified', modified)
    # --- installed apps / services / tasks / processes ---
    def keyed(rows, k): return {r.get(k, ''): r for r in rows}
    for name, key, cols in [('installed-apps.csv', 'PSChildName', ['DisplayName', 'DisplayVersion', 'Publisher', 'InstallLocation', 'UninstallString']),
                            ('live/services.csv', 'Name', ['DisplayName', 'Status', 'StartType']),
                            ('live/processes.csv', 'CommandLine', ['Name', 'ExecutablePath']),
                            ('appx-packages.csv', 'PackageFullName', ['Name', 'InstallLocation'])]:
        bb, ff = keyed(read_csv(os.path.join(a.before, name)), key), keyed(read_csv(os.path.join(a.after, name)), key)
        add = [k for k in ff if k not in bb]; rem = [k for k in bb if k not in ff]
        if add or rem:
            P(f'\n## {name}: +{len(add)} / -{len(rem)}')
            for k in add: P('- **+** `' + k + '` — ' + ' | '.join(f"{c}={ff[k].get(c,'')}" for c in cols))
            for k in rem: P('- **−** `' + k + '`')
    # scheduled tasks (schtasks CSV has odd header; use raw TaskName column)
    def tasks(d):
        rows = read_csv(os.path.join(d, 'live', 'scheduled-tasks.csv')); return {r.get('TaskName', ''): r for r in rows if r.get('TaskName', '') != 'TaskName'}
    tb, tf = tasks(a.before), tasks(a.after)
    add = [k for k in tf if k not in tb]
    if add:
        P(f'\n## Scheduled tasks added ({len(add)})')
        for k in add: P(f"- `{k}` → `{tf[k].get('Task To Run','')}` (next: {tf[k].get('Next Run Time','')})")
    # prefetch
    pb = {os.path.basename(p) for p in b if p.lower().startswith('c:\\windows\\prefetch\\')}
    pf = {os.path.basename(p) for p in f if p.lower().startswith('c:\\windows\\prefetch\\')}
    newpf = sorted(pf - pb)
    if newpf: P(f'\n## New Prefetch files ({len(newpf)})'); [P(f'- `{p}`') for p in newpf]
    # registry
    rb, rf = reg_index(a.before), reg_index(a.after)
    P('\n## Registry deltas')
    for fname in sorted(set(rb) | set(rf)):
        kb, kf = rb.get(fname, {}), rf.get(fname, {})
        newk = [k for k in kf if k not in kb and flt in k.lower()]
        chg = [k for k in kf if k in kb and kf[k] != kb[k] and flt in k.lower()]
        if not newk and not chg: continue
        P(f'\n### {fname}: +{len(newk)} keys, {len(chg)} changed')
        for k in newk[:a.max]:
            P(f'- **+** `{k}`'); [P(f'    - {v[:200]}') for v in sorted(kf[k])[:12]]
        for k in chg[:a.max]:
            dv = sorted(kf[k] - kb[k])
            if dv: P(f'- **~** `{k}`'); [P(f'    - {v[:200]}') for v in dv[:12]]
    rep = W.getvalue()
    if a.out: open(a.out, 'w').write(rep); print(f'wrote {a.out} ({len(rep)} chars)')
    else: print(rep)

if __name__ == '__main__': main()
