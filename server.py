#!/usr/bin/env python3
"""
Multi-threaded Dual-Stack (IPv4 + IPv6) Proxy & HTTP Server pro xcc2
- Běží na všech rozhraních (včetně Tailscale 100.x.y.z i IPv6)
- Threading: zvládá souběžná připojení z více zařízení najednou bez zasekávání
- Přeposílá veškeré *.json a /files/* požadavky na PLC http://192.168.0.122
"""

import http.server
import socket
import urllib.request
import urllib.error
import urllib.parse
import os
import sys
import subprocess

PORT = 8080
TARGET_BACKEND = "http://192.168.0.122"

class DualStackThreadingServer(http.server.ThreadingHTTPServer):
    address_family = socket.AF_INET6
    daemon_threads = True

    def server_bind(self):
        # Povolit duální stack (IPv4 i IPv6 na stejném portu)
        try:
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        except (AttributeError, OSError):
            pass
        super().server_bind()

class ProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Globální CORS hlavičky pro bezproblémové volání z jakéhokoliv zařízení
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Accept, Cookie, Authorization')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

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
        
        # Přeposlání hlaviček s výjimkou Host a Content-Length
        for header, value in self.headers.items():
            if header.lower() not in ['host', 'content-length']:
                req.add_header(header, value)

        try:
            with urllib.request.urlopen(req, timeout=6) as response:
                self.send_response(response.status)
                for header, value in response.headers.items():
                    if header.lower() not in ['transfer-encoding', 'content-length', 'access-control-allow-origin']:
                        self.send_header(header, value)
                content = response.read()
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for header, value in e.headers.items():
                if header.lower() not in ['transfer-encoding', 'content-length', 'access-control-allow-origin']:
                    self.send_header(header, value)
            content = e.read()
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(502, f"Chyba spojeni s PLC ({TARGET_BACKEND}): {e}")

def get_ips():
    ips = {'local': [], 'tailscale': []}
    try:
        out = subprocess.check_output(['ifconfig'], text=True)
        for line in out.splitlines():
            line = line.strip()
            if line.startswith('inet '):
                ip = line.split()[1]
                if ip.startswith('100.'):
                    ips['tailscale'].append(ip)
                elif not ip.startswith('127.'):
                    ips['local'].append(ip)
    except Exception:
        pass
    return ips

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    DualStackThreadingServer.allow_reuse_address = True
    
    ips = get_ips()
    tailscale_ip = ips['tailscale'][0] if ips['tailscale'] else "100.x.y.z"
    local_ip = ips['local'][0] if ips['local'] else "192.168.0.x"

    print("================================================================")
    print(" xcc2 Web Server připraven (Multithreaded Dual-Stack IPv4/IPv6)")
    print("================================================================")
    print(f" 💻 Lokálně na Macu:        http://localhost:{PORT}")
    print(f" 📱 V domácí síti (LAN):    http://{local_ip}:{PORT}")
    print(f" 🌐 Z mobilu přes Tailscale: http://{tailscale_ip}:{PORT}")
    print(f" 🎯 Cílový PLC kontroler:   {TARGET_BACKEND}")
    print("================================================================")
    print(" Naslouchám všem příchozím spojením...")

    try:
        server = DualStackThreadingServer(('::', PORT), ProxyHTTPRequestHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer ukončen.")
        sys.exit(0)
    except Exception as e:
        # Fallback na IPv4 pokud IPv6 není na systému povolen
        print(f"Přepínám na čistý IPv4 režim ({e})...")
        class IPv4ThreadingServer(http.server.ThreadingHTTPServer):
            daemon_threads = True
        server = IPv4ThreadingServer(('0.0.0.0', PORT), ProxyHTTPRequestHandler)
        server.serve_forever()
