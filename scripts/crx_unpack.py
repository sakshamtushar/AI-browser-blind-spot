import sys, struct, zipfile, io, json, os, hashlib
src, dst = sys.argv[1], sys.argv[2]
data = open(src,'rb').read()
assert data[:4]==b'Cr24', 'not a crx'
ver, hlen = struct.unpack('<II', data[4:12])
zbytes = data[12+hlen:]
os.makedirs(dst, exist_ok=True)
z = zipfile.ZipFile(io.BytesIO(zbytes)); z.extractall(dst)
m = json.load(open(os.path.join(dst,'manifest.json'), encoding='utf-8-sig'))
print(json.dumps({'file':os.path.basename(src),'crx_version':ver,'sha256':hashlib.sha256(data).hexdigest(),'name':m.get('name'),'version':m.get('version'),'manifest_version':m.get('manifest_version'),
  'permissions':m.get('permissions'),'host_permissions':m.get('host_permissions'),'background':m.get('background'),'content_scripts':[ {'matches':c.get('matches'),'js':c.get('js')} for c in m.get('content_scripts',[])],
  'web_accessible_resources':m.get('web_accessible_resources'),'externally_connectable':m.get('externally_connectable'),'update_url':m.get('update_url'),'key_present':'key' in m, 'files':len(z.namelist())}, indent=1))
