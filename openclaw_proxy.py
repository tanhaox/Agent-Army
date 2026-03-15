#!/usr/bin/env python3
"""OpenClaw Control UI 代理 - 支持完整 HTML 页面"""
import http.server
import base64
from urllib.request import urlopen, Request
import os

PASSWORD = "openclaw123"
TARGET_URL = "http://127.0.0.1:18791/"
AUTH_HEADER = "Basic " + base64.b64encode(f":{PASSWORD}".encode()).decode()

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # 处理根路径，重定向到 index.html
        if self.path == '/':
            self.path = '/'

        # 构建完整 URL
        url = TARGET_URL + self.path

        # 添加认证头
        req = Request(url)
        req.add_header("Authorization", AUTH_HEADER)

        # 复制其他请求头
        for header in ['User-Agent', 'Accept', 'Accept-Language', 'Connection']:
            if header in self.headers:
                req.add_header(header, self.headers[header])

        try:
            with urlopen(req) as response:
                content = response.read()
                self.send_response(200)

                # 复制响应头
                for header, value in response.headers.items():
                    if header.lower() in ['content-type', 'content-length', 'cache-control']:
                        self.send_header(header, value)

                # 添加 CORS 头以支持跨域请求
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', '*')

                self.end_headers()

                # 如果是 HTML，注入一些脚本以支持 WebSocket
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' in content_type:
                    # 注入 WebSocket 代理脚本
                    script = '''
<script>
// WebSocket 代理
const OriginalWebSocket = window.WebSocket;
window.WebSocket = function(url, protocols) {
    const wsUrl = url.replace('ws://localhost:18791', 'ws://127.0.0.1:18791');
    const ws = new OriginalWebSocket(wsUrl, protocols);

    // 添加认证
    const originalOnopen = ws.onopen;
    ws.onopen = function(e) {
        ws.send(JSON.stringify({type: 'auth', token: '%s'}));
        if (originalOnopen) originalOnopen.call(ws, e);
    };

    return ws;
};
</script>
''' % PASSWORD.replace("'", "\\'")

                    # 在 </head> 前注入脚本
                    if b'</head>' in content:
                        content = content.replace(b'</head>', script.encode() + b'</head>')

                self.wfile.write(content)

        except Exception as e:
            print(f"Error: {e}")
            self.send_error(500, str(e))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length else b''

        url = TARGET_URL + self.path
        req = Request(url, data=post_data, method='POST')
        req.add_header("Authorization", AUTH_HEADER)
        req.add_header("Content-Type", self.headers.get('Content-Type', 'application/json'))

        try:
            with urlopen(req) as response:
                content = response.read()
                self.send_response(200)
                for header, value in response.headers.items():
                    if header.lower() in ['content-type', 'content-length']:
                        self.send_header(header, value)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(content)
        except Exception as e:
            self.send_error(500, str(e))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def log_message(self, format, *args):
        pass  # 静默模式

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    server = http.server.HTTPServer(('127.0.0.1', 18792), ProxyHandler)
    print("OpenClaw Control UI Proxy")
    print("=" * 50)
    print("Access: http://127.0.0.1:18792/")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    server.serve_forever()
