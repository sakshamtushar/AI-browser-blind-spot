#!/usr/bin/env python3
"""hva_compare.py: Phase 3 person-vs-agent comparison (see RUNBOOK-phase3-human-vs-agent.md).

Pulls, from a collect.ps1 bundle, every field that could tell a person's browsing from an
agent's, and labels each row with the run it falls in.

  hva_compare.py AFTER_BUNDLE [--before BEFORE_BUNDLE] [--profile 'Perplexity_Comet_User_Data/Profile 1']
                 [--runs runs.csv] [--telemetry hva-telemetry.jsonl] [--url-like %8088%] -o OUTDIR

runs.csv columns: run_id,actor,task,start_utc,end_utc   (ISO 8601 UTC; actor = P | A | S)

Writes OUTDIR/visits.csv, autofill.csv, sessions.csv, extdiff.csv, telemetry.csv and summary.md.
Reads copies only (sqlite immutable=1, files opened read-only). Never prints field values
other than C0C0N canary strings.
"""
import argparse, csv, datetime as dt, json, pathlib, sqlite3, sys
from ccl_chromium_reader import ccl_chromium_snss2 as snss
from ccl_chromium_reader.storage_formats import ccl_leveldb

CORE = {0: 'LINK', 1: 'TYPED', 2: 'AUTO_BOOKMARK', 3: 'AUTO_SUBFRAME', 4: 'MANUAL_SUBFRAME', 5: 'GENERATED',
        6: 'AUTO_TOPLEVEL', 7: 'FORM_SUBMIT', 8: 'RELOAD', 9: 'KEYWORD', 10: 'KEYWORD_GENERATED'}
QUAL = {0x00800000: 'BLOCKED', 0x01000000: 'FORWARD_BACK', 0x02000000: 'FROM_ADDRESS_BAR', 0x04000000: 'HOME_PAGE',
        0x08000000: 'FROM_API', 0x10000000: 'CHAIN_START', 0x20000000: 'CHAIN_END',
        0x40000000: 'CLIENT_REDIRECT', 0x80000000: 'SERVER_REDIRECT'}
VISIT_SOURCE = {0: 'SYNCED', 1: 'BROWSED', 2: 'EXTENSION', 3: 'FIREFOX_IMPORTED', 4: 'IE_IMPORTED', 5: 'SAFARI_IMPORTED'}
EPOCH = dt.datetime(1601, 1, 1, tzinfo=dt.timezone.utc)


def transition(t):
    t &= 0xFFFFFFFF
    return CORE.get(t & 0xFF, str(t & 0xFF)), '|'.join(n for b, n in QUAL.items() if t & b)


def wk(us):  # WebKit microseconds -> aware datetime
    return EPOCH + dt.timedelta(microseconds=int(us)) if us else None


def iso(d):
    return d.isoformat(timespec='milliseconds').replace('+00:00', 'Z') if d else ''


def load_runs(path):
    runs = []
    if path:
        for r in csv.DictReader(open(path, newline='')):
            r['start'] = dt.datetime.fromisoformat(r['start_utc'].replace('Z', '+00:00'))
            r['end'] = dt.datetime.fromisoformat(r['end_utc'].replace('Z', '+00:00'))
            runs.append(r)
    return runs


def label(runs, when):
    for r in runs:
        if when and r['start'] <= when <= r['end']:
            return r['run_id'], r['actor'], r['task']
    return '', '', ''


def profile_dir(bundle, sub):
    hits = [p for p in (pathlib.Path(bundle) / 'profiles').glob('*') if sub.split('/')[0] in p.name]
    if not hits:
        sys.exit(f'no profile matching {sub!r} under {bundle}/profiles')
    return hits[0] / sub.split('/', 1)[1] if '/' in sub else hits[0]


def db(path):
    return sqlite3.connect(f'file:{path}?immutable=1', uri=True)


def visits(prof, url_like, runs):
    con = db(prof / 'History')
    cols = {r[1] for r in con.execute('PRAGMA table_info(context_annotations)')}
    ctx = ', c.tab_id, c.task_id, c.parent_task_id, c.root_task_id, c.page_end_reason, c.total_foreground_duration' if 'tab_id' in cols else ''
    q = f'''SELECT v.id, v.visit_time, u.url, v.transition, v.from_visit, v.opener_visit, v.visit_duration, u.typed_count,
                   (SELECT source FROM visit_source s WHERE s.id = v.id) {ctx}
            FROM visits v JOIN urls u ON u.id = v.url
            LEFT JOIN context_annotations c ON c.visit_id = v.id
            WHERE u.url LIKE ? ORDER BY v.visit_time'''
    out = []
    for row in con.execute(q, (url_like,)):
        vid, vt, url, tr, frm, opn, dur, typed, src, *c = row + (None,) * (6 - (len(row) - 9))
        when = wk(vt)
        core, qual = transition(tr)
        rid, actor, task = label(runs, when)
        out.append(dict(run=rid, actor=actor, task=task, visit_id=vid, time=iso(when), url=url, core=core, qualifiers=qual,
                        from_visit=frm, opener_visit=opn, duration_s=round((dur or 0) / 1e6, 3), typed_count=typed,
                        visit_source=VISIT_SOURCE.get(src, 'BROWSED (no row)' if src is None else src),
                        tab_id=c[0], task_id=c[1], parent_task_id=c[2], root_task_id=c[3], page_end_reason=c[4],
                        foreground_s=round(c[5] / 1e6, 3) if c[5] and c[5] > 0 else ''))
    return out


def autofill(prof, runs, page_visits):
    out = []
    for name, value, created, used, count in db(prof / 'Web Data').execute(
            "SELECT name, value, date_created, date_last_used, count FROM autofill WHERE value LIKE 'C0C0N-CANARY-%'"):
        when = dt.datetime.fromtimestamp(created, dt.timezone.utc)
        prior = [v for v in page_visits if v['time'] and v['time'] <= iso(when) and v['core'] != 'FORM_SUBMIT']
        gap = (when - dt.datetime.fromisoformat(prior[-1]['time'].replace('Z', '+00:00'))).total_seconds() if prior else ''
        rid, actor, task = label(runs, when)
        out.append(dict(run=rid, actor=actor, task=task, field=name, canary=value, created=iso(when),
                        last_used=iso(dt.datetime.fromtimestamp(used, dt.timezone.utc)), count=count,
                        secs_after_page_visit=gap))
    return out


def sessions(prof, url_like, runs):
    """Navigation entries for matching URLs plus tab-group commands, from every SNSS file in Sessions/."""
    needle = url_like.strip('%')
    out = []
    for f in sorted((prof / 'Sessions').glob('*')):
        with open(f, 'rb') as fh:
            s = snss.SnssFile(snss.SnssFileType.Session if f.name.startswith('Session') else snss.SnssFileType.Tab, fh)
            # newer Chromium writes command ids this parser predates; map them to a skipped (unprocessed) id
            enum = snss.SessionRestoreIdType if s.file_type == snss.SnssFileType.Session else snss.TabRestoreIdType
            skip = next(e for e in enum if e.name != 'CommandUpdateTabNavigation')
            s._id_type = lambda v, enum=enum, skip=skip: enum(v) if v in {e.value for e in enum} else skip
            for cmd in s.iter_session_commands():
                if isinstance(cmd, snss.NavigationEntry) and needle in (cmd.url or ''):
                    core, qual = transition(int(cmd.transition_type.value if hasattr(cmd.transition_type, 'value') else cmd.transition_type))
                    when = cmd.timestamp if isinstance(cmd.timestamp, dt.datetime) else None
                    if when and when.tzinfo is None:
                        when = when.replace(tzinfo=dt.timezone.utc)
                    rid, actor, task = label(runs, when)
                    out.append(dict(run=rid, actor=actor, task=task, file=f.name, kind='navigation', session_id=cmd.session_id,
                                    index=cmd.index, time=iso(when), url=cmd.url, core=core, qualifiers=qual,
                                    has_post_data=cmd.has_post_data, ua_override=cmd.is_overriding_user_agent,
                                    task_id=cmd.task_id, root_task_id=cmd.root_task_id, detail=''))
                elif getattr(cmd, 'id_type', None) in (snss.SessionRestoreIdType.CommandSetTabGroup,
                                                       snss.SessionRestoreIdType.CommandSetTabGroupMetadata,
                                                       snss.SessionRestoreIdType.CommandSetTabGroupMetadata2):
                    out.append(dict(run='', actor='', task='', file=f.name, kind=cmd.id_type.name, session_id='', index='',
                                    time='', url='', core='', qualifiers='', has_post_data='', ua_override='',
                                    task_id='', root_task_id='', detail=f'offset {cmd.offset}'))
    return out


def leveldb_keys(path):
    keys = {}
    try:
        for rec in ccl_leveldb.RawLevelDb(path).iterate_records_raw():
            keys[bytes(rec.user_key)] = (rec.state.name, len(rec.value or b''), rec.seq)
    except Exception as e:  # noqa: BLE001 - a damaged store should not stop the whole run
        keys[b'<error>'] = (str(e)[:80], 0, 0)
    return keys


def extdiff(before, after):
    """Key-level diff of every extension LevelDB store (catches task state that holds no canary)."""
    out = []
    stores = lambda p: {s.relative_to(p).as_posix(): s for pat in ('Local Extension Settings/*', 'IndexedDB/chrome-extension_*leveldb', 'Sync Extension Settings/*')
                        for s in p.glob(pat) if s.is_dir()}
    b, a = stores(before) if before else {}, stores(after)
    for name in sorted(set(a) | set(b)):
        kb = leveldb_keys(b[name]) if name in b else {}
        ka = leveldb_keys(a[name]) if name in a else {}
        for k in sorted(set(ka) | set(kb)):
            if ka.get(k) != kb.get(k):
                change = 'added' if k not in kb else 'removed' if k not in ka else 'changed'
                st = ka.get(k) or kb.get(k)
                out.append(dict(store=name, change=change, key=k[:120].decode('utf-8', 'backslashreplace'),
                                state=st[0], value_bytes=st[1], seq=st[2]))
    return out


def telemetry(path, runs):
    out = []
    for line in open(path, encoding='utf-8') if path else []:
        r = json.loads(line)
        when = dt.datetime.fromisoformat(r['serverTime']).astimezone(dt.timezone.utc)
        rid, actor, task = label(runs, when)
        typed_len = (r.get('fieldLengths') or {}).get('name', '')
        out.append(dict(run=rid, actor=actor, task=task, page=r.get('page'), reason=r.get('sentReason'), canary=r.get('canary', ''),
                        ms_on_page=r.get('msOnPage'), first_interaction_ms=r.get('firstInteractionMs'), keys=r.get('keys'),
                        keys_untrusted=r.get('keysUntrusted'), pastes=r.get('pastes'), inputs=json.dumps(r.get('inputs')),
                        pointer_moves=r.get('pointerMoves'), pointer_untrusted=r.get('pointerMovesUntrusted'),
                        clicks_trusted=sum(1 for c in r.get('clicks', []) if c.get('trusted')), clicks=len(r.get('clicks', [])),
                        moves_before_first_click=(r.get('clicks') or [{}])[0].get('movesBefore', ''),
                        name_len=typed_len, webdriver=r.get('webdriver'), focus_order='>'.join(r.get('focusOrder', []))))
    return out


def write(path, rows):
    if not rows:
        path.write_text('')
        return
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('after'); ap.add_argument('--before')
    ap.add_argument('--profile', default='Perplexity_Comet_User_Data/Profile 1')
    ap.add_argument('--runs'); ap.add_argument('--telemetry'); ap.add_argument('--url-like', default='%8088%')
    ap.add_argument('-o', '--out', required=True)
    a = ap.parse_args()
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    runs = load_runs(a.runs)
    prof = profile_dir(a.after, a.profile)
    v = visits(prof, a.url_like, runs)
    tables = dict(visits=v, autofill=autofill(prof, runs, v), sessions=sessions(prof, a.url_like, runs),
                  extdiff=extdiff(profile_dir(a.before, a.profile) if a.before else None, prof),
                  telemetry=telemetry(a.telemetry, runs))
    for name, rows in tables.items():
        write(out / f'{name}.csv', rows)
    lines = [f'# hva_compare: {a.after}', f'profile `{a.profile}`, before `{a.before or "-"}`, {len(runs)} runs', '']
    for name, rows in tables.items():
        lines.append(f'- {name}: {len(rows)} rows')
    lines += ['', '## Visits (transition fingerprint)', '| run | actor | time | url | core | qualifiers | from | opener | source | tab |', '|---|---|---|---|---|---|---|---|---|---|']
    lines += [f"| {r['run']} | {r['actor']} | {r['time']} | {r['url'].split('/', 3)[-1]} | {r['core']} | {r['qualifiers']} | {r['from_visit']} | {r['opener_visit']} | {r['visit_source']} | {r['tab_id']} |" for r in v]
    (out / 'summary.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
