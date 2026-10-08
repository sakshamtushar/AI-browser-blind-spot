import json, sys, os
ud = sys.argv[1]
ls = json.load(open(os.path.join(ud, 'Local State'), encoding='utf-8'))
print('Local State top keys:', sorted(ls.keys()))
oc = ls.get('os_crypt', {})
print('os_crypt keys:', {k: (v[:20] + '...' if isinstance(v, str) else v) for k, v in oc.items()})
for f in ('Secure Preferences', 'Preferences'):
    p = os.path.join(ud, 'Default', f)
    if not os.path.exists(p): continue
    d = json.load(open(p, encoding='utf-8'))
    ext = d.get('extensions', {}).get('settings', {})
    print(f'\n== {f}: {len(ext)} extensions')
    for eid, e in ext.items():
        m = e.get('manifest', {})
        print(f"  {eid}  loc={e.get('location')} state={e.get('state')} from_webstore={e.get('from_webstore')} name={m.get('name')!r} v={m.get('version')} path={e.get('path')} install_time={e.get('install_time')}")
        if eid.startswith('ahfpellj'):
            print('     perms:', m.get('permissions'), 'hosts:', m.get('host_permissions'), 'desc:', m.get('description'))
            print('     bg:', m.get('background'), 'cs:', [c.get('matches') for c in m.get('content_scripts', [])])
    # any perplexity/comet-namespaced prefs
    def walk(o, path=''):
        if isinstance(o, dict):
            for k, v in o.items():
                kp = f'{path}.{k}' if path else k
                if any(s in k.lower() for s in ('perplexity', 'comet', 'sidecar', 'assistant', 'agent', 'dxt', 'mcp')):
                    print('  PREF', kp, '=', json.dumps(v)[:160])
                walk(v, kp)
    print(f'-- {f} interesting keys:'); walk(d)
