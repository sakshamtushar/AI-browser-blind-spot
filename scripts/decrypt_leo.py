"""decrypt_leo.py <UserData> — decrypt Brave Leo AIChat entries (v10, DPAPI-wrapped key) and show v20 (ABE) cookies fail with the same key. Run as the profile's user on Windows."""
import sys, os, json, base64, sqlite3, ctypes, ctypes.wintypes as wt, re
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
UD = sys.argv[1]
class DATA_BLOB(ctypes.Structure): _fields_ = [('cbData', wt.DWORD), ('pbData', ctypes.POINTER(ctypes.c_char))]
def dpapi_unprotect(b):
    inp = DATA_BLOB(len