"""ext_teardown_redacted.py <copied LES dir> <label> — keys-only, content-redacted dump of a
chrome.storage.local LevelDB. Emits key names, value sizes, numeric values (timestamps), and a
JSON *skeleton* where every string is replaced by <str:len>. No real content is ever printed."""
import sys, json
from ccl_chromium_reader.storage_formats import ccl_leveldb
SECRETISH = ('token','secret','key','auth','password','cred','session','cookie','apikey','api_key','bearer','jwt')
def redact(o, depth=0):
    if isinstance(o, str): return f"<str:{len(o)}>"
    if isinstance(o, dict): return {k: redact(v, depth+1) for k, v in o.items()}
    if isinstance(o, list):
        r = [redact(x, depth+1) for x in o[:4]]
        if len(o) > 4: r.append(f"<+{len(o)-4} more>")
        return r
    return o  # int/float/bool/None kept (timestamps, flags)
d, label = sys.argv[1], sys.argv[2]
print(f"# {label}  ({d})")
db = ccl_leveldb.RawLevelDb(d)
rows = list(db.iterate_records_raw())
print(f"{len(rows)} records (live+deleted)\n")
for rec in rows:
    k = rec.user_key.decode('utf-8','replace')
    v = rec.value
    flag = '  <<SECRET-SHAPED KEY>>' if any(s in k.lower() for s in SECRETISH) else ''
    st = rec.state.name
    try:
        skel = json.dumps(redact(json.loads(v.decode('utf-8'))))
        print(f"[{st}] {k}  ({len(v)}B){flag}\n      shape: {skel[:400]}")
    except Exception:
        print(f"[{st}] {k}  ({len(v)}B non-json, head={v[:6].hex()}){flag}")
db.close()
