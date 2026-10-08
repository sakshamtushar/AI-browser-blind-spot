import http.server, socketserver, datetime, urllib.parse, os, json
os.chdir(os.path.dirname(os.path.abspath(__file__)))
class H(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0)); body = self.rfile.read(n).decode(errors='replace')
        if self.path.startswith('/telemetry'):  # Phase 3: hva.js interaction summary, one JSON object per line
            try: rec = json.loads(body)
            except ValueError: rec = {'unparsed': body[:2000]}
            rec.update(serverTime=datetime.datetime.now().isoformat(), client=self.client_address[0], ua=self.headers.get('User-Agent'))
            with open('hva-telemetry.jsonl', 'a', encoding='utf-8') as f: f.write(json.dumps(rec) + '\n')
            self.send_response(204); self.end_headers(); return
        with open('form-log.txt', 'a', encoding='utf-8') as f:
            f.write(f"{datetime.datetime.now().isoformat()} {self.client_address[0]} UA={self.headers.get('User-Agent')} {urllib.parse.unquote_plus(body)}\n")
        self.send_response(200); self.send_header('Content-Type', 'text/html'); self.end_headers()
        self.wfile.write(b'<html><body><h1>Request received</h1><p>Reference C0C0N-FORM-OK</p></body></html>')
    def log_message(self, fmt, *a):
        with open('access-log.txt', 'a', encoding='utf-8') as f:
            f.write(f"{datetime.datetime.now().isoformat()} {self.client_address[0]} UA={self.headers.get('User-Agent')} {fmt % a}\n")
socketserver.ThreadingTCPServer.allow_reuse_address = True
with socketserver.ThreadingTCPServer(('0.0.0.0', int(os.environ.get('LAB_PORT', 8088))), H) as s: s.serve_forever()
