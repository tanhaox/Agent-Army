# 启动HTTP服务器来提供网页服务
import http.server
import socketserver
import os
import json
from urllib.parse import urlparse, parse_qs

PORT = 54321

# 设置工作目录
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(WORK_DIR)

# 自定义处理器
class NewsHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WORK_DIR, **kwargs)

    def do_GET(self):
        # 处理API请求
        if self.path.startswith('/api/'):
            self.handle_api_request()
        else:
            # 处理静态文件请求
            super().do_GET()

    def handle_api_request(self):
        if self.path == '/api/news':
            self.send_json_response(self.get_news_data())
        else:
            self.send_404()

    def get_news_data(self):
        try:
            # 读取新闻数据文件
            data_file = os.path.join(WORK_DIR, 'news_data.json')
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data
            else:
                return []
        except Exception as e:
            print(f"Error reading news data: {e}")
            return []

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(json_data.encode('utf-8'))

    def send_404(self):
        self.send_response(404)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(b'Not Found')

# 启动服务器
try:
    with socketserver.TCPServer(('', PORT), NewsHandler) as httpd:
        print(f"服务器启动成功，端口: {PORT}")
        print(f"访问地址: http://localhost:{PORT}/news_dashboard.html")
        print("按 Ctrl+C 停止服务器")
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\n服务器已停止")
except Exception as e:
    print(f"服务器启动失败: {e}")