import sys, pathlib, re, json
from ccl_chromium_reader import ccl_chromium_indexeddb as idb
p = pathlib.Path(sys.argv[1]); blob = pathlib.Path(str(p).replace('.leveldb', '.blob'))
maxrec = int(sys.argv[2]) if len(sys.argv) > 2 else 8
SECRET = re.compile(r'(\+?91[ -]?[0-9]{10}|[0-9]{10}|leosectrainings(@gmail\.com)?|sk-[A-Za-z0-9_-]{16,}|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{6,})')
wrapper = idb.WrappedIndexDB(p, blob if blob.exists() else None)
for db_id in wrapper.database_ids:
    db = wrapper[db_id.dbid_no]
    print(f'## DB {db.name!r} (id {db_id.dbid_no}) origin={db_id.origin!r}')
    for os_name in db.object_store_names:
        st = db[os_name]
        recs = list(st.iterate_records(live_only=False))
        live = sum(1 for r in recs if r.is_live)
        print(f'  ### store {os_name!r}: {len(recs)} records ({live} live)')
        for r in recs[:maxrec]:
            v = r.value
            s = json.dumps(v, default=str)[:300] if not isinstance(v, (bytes, bytearray)) else f'<bytes {len(v)}>'
            print(f'    [{"live" if r.is_live else "DELETED"}] key={str(r.key.value)[:80]!r} -> {SECRET.sub("[REDACTED]", s)}')
