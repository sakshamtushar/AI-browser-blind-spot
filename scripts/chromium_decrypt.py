"""chromium_decrypt.py — run ON the Windows VM as the profile owner (DPAPI-bound).
Decrypts Chromium 'v10' OSCrypt blobs (cookies, Login Data, Brave AIChat entry_text) using the
per-user DPAPI key in Local State. Reports 'v20' (App-Bound Encryption) blobs as needing the
elevation service. Prints REDACTED output. Usage: chromium_decrypt.py <User Data dir> <profile subdir>
"""
import sys, os, json, base64, sqlite3, shutil, re, ctypes, ctypes.wintypes as w, tempfile
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except Exception as e:
    print("MISSING cryptography:", e); sys.exit(2)

class BLOB(ctypes.Structure):
    _fields_ = [("cbData", w.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]
def dpapi_unprotect(data):
    bin_ = BLOB(len(data), ctypes.cast(ctypes.c_char_p(data), ctypes.POINTER(ctypes.c_char)))
    out = BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(bin_), None, None, None, None, 0, ctypes.byref(out)):
        raise ctypes.WinError()
    buf = ctypes.string_at(out.pbData, out.cbData); ctypes.windll.kernel32.LocalFree(out.pbData); return buf

REDACT = re.compile(r'(\+?91[ -]?[0-9]{10}|leosectrainings(@gmail\.com)?|sk-[A-Za-z0-9_-]{16,}|eyJ[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{6,})')
def red(s): return REDACT.sub('[REDACTED]', s)

ud, prof = sys.argv[1], sys.argv[2]
ls = json.load(open(os.path.join(ud, 'Local State'), encoding='utf-8'))
oc = ls['os_crypt']
print('os_crypt keys:', list(oc))
key = None
if 'encrypted_key' in oc:
    enc = base64.b64decode(oc['encrypted_key'])
    print('encrypted_key prefix:', enc[:5])
    if enc[:5] == b'DPAPI':
        key = dpapi_unprotect(enc[5:]); print('v10 AES key recovered via user-DPAPI:', len(key), 'bytes')
abe = 'app_bound_encrypted_key' in oc
print('app_bound_encrypted_key present:', abe)

def dec_v10(blob):
    if key is None: return None, 'no-v10-key'
    try:
        pt = AESGCM(key).decrypt(blob[3:15], blob[15:], None)
        return pt, 'v10'
    except Exception as e:
        return None, f'v10-fail:{e}'

def classify(blob):
    if not blob: return '', 'empty'
    if blob[:3] == b'v10':
        pt, how = dec_v10(blob)
        if pt is None: return '', how
        # cookie/login plaintext in v10+ is prefixed by 32-byte SHA256(domain); strip if non-text
        if len(pt) > 32 and not pt[:32].decode('utf-8','ignore').isprintable():
            body = pt[32:]
        else:
            body = pt
        try: return body.decode('utf-8','replace'), 'v10'
        except: return repr(body[:60]), 'v10-bytes'
    if blob[:3] == b'v20': return '', 'v20-APP-BOUND (needs elevation service)'
    return '', f'plaintext/other({blob[:4]!r})'

tmp = tempfile.mkdtemp()
def copyq(src):
    dst = os.path.join(tmp, os.path.basename(src) + str(abs(hash(src))%9999))
    try: shutil.copy(src, dst); return dst
    except PermissionError:
        os.system(f'esentutl /y "{src}" /d "{dst}" >nul 2>&1')
        return dst if os.path.exists(dst) else None

pdir = os.path.join(ud, prof)
# --- Cookies ---
for rel in ('Network/Cookies', 'Cookies'):
    p = os.path.join(pdir, rel.replace('/', os.sep))
    if os.path.exists(p):
        cp=copyq(p)
        if not cp: print(f'\n== {rel} == LOCKED/uncopyable'); continue
        con = sqlite3.connect(cp); n=v10=v20=0
        print(f'\n== {rel} ==')
        for host, name, ev in con.execute('select host_key,name,encrypted_value from cookies'):
            n+=1; val, how = classify(ev)
            if how.startswith('v10'): v10+=1
            elif how.startswith('v20'): v20+=1
            if n<=6 or 'perplexity' in host or 'brave' in host:
                print(f'  {host} {name} [{how}] = {red(val)[:60]!r}')
        print(f'  totals: {n} cookies, v10-decrypted={v10}, v20-appbound={v20}')
        con.close()
# --- Login Data ---
p = os.path.join(pdir, 'Login Data')
if os.path.exists(p):
    cp=copyq(p)
    con = sqlite3.connect(cp) if cp else None
    print('\n== Login Data ==' + ('' if cp else ' LOCKED'))
    if con:
     for url, u, pw in con.execute('select origin_url,username_value,password_value from logins'):
        val, how = classify(pw); print(f'  {url} user={red(u)} [{how}] pw={red(val)[:20]!r}')
     con.close()
# --- Brave AIChat ---
p = os.path.join(pdir, 'AIChat')
if os.path.exists(p):
    cp=copyq(p)
    con = sqlite3.connect(cp); print('\n== AIChat conversation_entry (decrypted) ==')
    for uuid, date, ctype, entry, model in con.execute('select uuid,date,character_type,entry_text,model_key from conversation_entry order by date'):
        val, how = classify(entry) if entry else ('', 'null')
        who = {0:'HUMAN',1:'ASSISTANT'}.get(ctype, ctype)
        print(f'  {who} model={model} [{how}] text={red(val)[:200]!r}')
    print('\n== AIChat conversation titles ==')
    for uuid, title in con.execute('select uuid,title from conversation'):
        val, how = classify(title) if title else ('','null'); print(f'  [{how}] {red(val)[:80]!r}')
    con.close()
shutil.rmtree(tmp, ignore_errors=True)
