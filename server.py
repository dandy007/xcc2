#!/usr/bin/env python3
"""
Lightweight Proxy & HTTP Server pro xcc2
- Servíruje lokální index.html na http://0.0.0.0:8080
- Přeposílá veškeré API požadavky (*.json, /files/*) na PLC backend http://192.168.0.122
- Řeší CORS a předávání autentizačních cookies pro prohlížeč na Macu i mobilu (přes Tailscale)
"""

import http.server
import socketserver
import urllib.request
import urllib.error
import urllib.parse
import os
import sys

PORT = 8080
TARGET_BACKEND = "http://192.168.0.122"

class ProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.endswith('.json') or self.path.startswith('/files/') or '.json?' in self.path:
            self.proxy_request('GET')
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.endswith('.json') or '.json?' in self.path:
            self.proxy_request('POST')
        else:
            self.send_error(404, "Not Found")

    def proxy_request(self, method):
        target_url = f"{TARGET_BACKEND}{self.path}"
        
        # Čtení těla POST požadavku
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        req = urllib.request.Request(target_url, data=body, method=method)
        
        # Přeposlání hlaviček
        for header, value in self.headers.items():
            if header.lower() not in ['host', 'content-length']:
                req.add_header(header, value)

        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                self.send_response(response.status)
                for header, value in response.headers.items():
                    if header.lower() not in ['transfer-encoding', 'content-length']:
                        self.send_header(header, value)
                content = response.read()
                self.send_header('Content-Length', str(len(content)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(content)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for header, value in e.headers.items():
                if header.lower() not in ['transfer-encoding', 'content-length']:
                    self.send_header(header, value)
            content = e.read()
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(502, f"Chyba spojeni s PLC ({TARGET_BACKEND}): {e}")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Accept')
        self.end_headers()

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), ProxyHTTPRequestHandler) as httpd:
        print(f"=======================================================")
        print(f" xcc2 web server běží na:")
        print(f" -> Lokálně:       http://localhost:{PORT}")
        print(f" -> Přes Tailscale: http://<tailscale-ip-macu>:{PORT}")
        print(f" -> Cílový PLC:     {TARGET_BACKEND}")
        print(f"=======================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nUkončeno.")
            sys.exit(0)
