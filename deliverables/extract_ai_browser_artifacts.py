#!/usr/bin/env python3
"""extract_ai_browser_artifacts.py — the missing "AI browser conversation & artifact extractor".
Point it at a Chromium-family User Data dir (Comet / Brave / Chrome / Edge, any OS). Read-only.
Pulls the AI layer that generic parsers skip: Brave Leo AIChat (schema + cleartext timeline;
decrypt the text on the owning host with scripts/decrypt_leo.py), Perplexity assistant prompt cache from
perplexity.ai IndexedDB, AI-extension chrome.storage.local (Claude/ChatGPT/comet-agent/HARPA/Sider),
Local Storage AI-token keys, and the Gemini glic storage partition. Emits key names + structure,
redacting string values unless --unsafe. Requires: pip install chromium-reader cryptography.
Deps reused from the c0c0n lab: ccl_chromium_reader.  Author: Saksham Tushar, c0c0n 2026.
"""
import argparse, os, json, sqlite3, glob, re, sys
AI_EXT = {  # known AI extension IDs -> label
 'fcoeoabgfenejglbffodgkkbkcdhcgfn':'Claude in Chrome','hehggadaopoacecdllhhajmbjkdcmajg':'ChatGPT',
 'mcjlamohcooanphmebaiigheeeoplihb':'Comet (built-in)','npclhjbddhklpbnacpjloidibaggcgon':'comet-agent (built-in)',
 'eanggfilgoajaocelnaflolkadkeghjp':'HARPA AI','difoiogjjojoaoomphldepapgpbgkhkb':'Sider','ofpnmcalabcbjgholdjcjblkibolbppb':'Monica'}
def redact(o):
    if isinstance(o,str): return f"<str:{len(o)}>"
    if isinstance(o,dict): return {k:redact(v) for k,v in o.items()}
    if isinstance(o,list): return [redact(x) for x in o[:4]]+([f"<+{len(o)-4}>"] if len(o)>4 else [])
    return o
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('userdata'); ap.add_argument('--unsafe',action='store_true',help='print raw values (PII!)')
    a=ap.parse_args(); UD=a.userdata; show=(lambda o:o) if a.unsafe else redact
    from ccl_chromium_reader.storage_formats import ccl_leveldb
    print(f"# AI-browser artifact extract: {UD}")
    profiles=[p for p in glob.glob(os.path.join(UD,'*')) if os.path.isdir(p) and os.path.exists(os.path.join(p,'Preferences'))]
    for prof in profiles:
        pn=os.path.basename(prof); print(f"\n## profile: {pn}")
        aic=os.path.join(prof,'AIChat')
        if os.path.exists(aic):
            c=sqlite3.connect(f'file:{aic}?mode=ro&immutable=1',uri=True)
            rows=c.execute("select date,character_type,model_key,length(entry_text) from conversation_entry order by date").fetchall()
            print(f"  [Brave Leo] AIChat: {len(rows)} entries (timeline+model cleartext; entry_text encrypted)")
            for d,ct,mk,ln in rows[:8]: print(f"     t={d} who={'HUMAN' if ct==0 else 'ASSISTANT'} model={mk} enc_text_len={ln}")
            c.close()
        for eid,label in AI_EXT.items():
            les=os.path.join(prof,'Local Extension Settings',eid)
            if os.path.isdir(les):
                db=ccl_leveldb.RawLevelDb(les); keys=[r.user_key.decode('utf-8','replace') for r in db.iterate_records_raw()]; db.close()
                sec=[k for k in set(keys) if re.search(r'token|secret|key|auth|permission|session',k,re.I)]
                print(f"  [ext {label} {eid}] {len(keys)} records; sensitive-shaped keys: {sorted(sec)[:12]}")
        idb=os.path.join(prof,'IndexedDB','https_www.perplexity.ai_0.indexeddb.leveldb')
        if os.path.isdir(idb): print(f"  [Comet] perplexity.ai IndexedDB present -> assistant prompt/thread cache (keyval-store); parse with ccl_chromium_indexeddb")
        glicp=glob.glob(os.path.join(prof,'Storage','ext','glic','*'))
        if glicp: print(f"  [Gemini] glic partition: {glicp[0]} (isolated Cookies/LocalStorage; SHA256('glicpart') dir)")
    nmh=os.path.join(UD,'NativeMessagingHosts')
    if os.path.isdir(nmh):
        print("\n## NativeMessagingHosts (AI-agent bridge map)")
        for j in glob.glob(os.path.join(nmh,'*.json')):
            try: d=json.load(open(j)); 
            except: continue
            if re.search(r'openai|anthropic|claude|codex|perplexity|comet',d.get('name',''),re.I):
                print(f"  {d.get('name')} -> {d.get('path')}  origins={d.get('allowed_origins')}")
if __name__=='__main__': main()
