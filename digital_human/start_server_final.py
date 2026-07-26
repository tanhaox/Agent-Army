# 稳定版HTTP服务器 - 用于新闻聚合系统
import http.server
import socketserver
import os
import json
import logging
import subprocess
import sys
from urllib.parse import urlparse, parse_qs

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PORT = 54321
WORK_DIR = os.path.dirname(os.path.abspath(__file__))

# 确保工作目录正确
os.chdir(WORK_DIR)
logger.info(f"工作目录: {WORK_DIR}")

class NewsHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # 设置正确的目录
        kwargs['directory'] = WORK_DIR
        super().__init__(*args, **kwargs)

    def do_GET(self):
        logger.info(f"请求路径: {self.path}")

        # 处理API请求
        if self.path.startswith('/api/'):
            self.handle_api_request()
        else:
            # 处理静态文件请求
            try:
                super().do_GET()
            except Exception as e:
                logger.error(f"静态文件处理错误: {e}")
                self.send_error(500, "服务器内部错误")

    def do_POST(self):
        logger.info(f"POST请求路径: {self.path}")

        # 处理POST请求
        if self.path == '/api/fetch_news':
            self.handle_fetch_news()
        else:
            self.send_404()

    def handle_api_request(self):
        try:
            if self.path == '/api/news':
                self.send_json_response(self.get_news_data())
            elif self.path == '/api/fetch_news':
                self.handle_fetch_news()
            else:
                self.send_404()
        except Exception as e:
            logger.error(f"API请求处理错误: {e}")
            self.send_error(500, "服务器内部错误")

    def handle_fetch_news(self):
        try:
            logger.info("开始执行新闻采集...")

            # 重新运行爬虫脚本
            result = subprocess.run([sys.executable, 'run_crawler_fixed.py'],
                                  cwd=WORK_DIR,
                                  capture_output=True,
                                  text=True,
                                  timeout=30)

            if result.returncode == 0:
                logger.info("新闻采集完成")
                self.send_json_response({"success": True, "message": "新闻采集完成"})
            else:
                logger.error(f"新闻采集失败: {result.stderr}")
                self.send_json_response({"success": False, "message": "新闻采集失败", "error": result.stderr})
        except Exception as e:
            logger.error(f"执行采集失败: {e}")
            self.send_error(500, f"执行采集失败: {e}")

    def get_news_data(self):
        try:
            data_file = os.path.join(WORK_DIR, 'news_data.json')
            logger.info(f"尝试读取数据文件: {data_file}")

            if os.path.exists(data_file):
                # 检查文件是否为空
                with open(data_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content and content != '[]':
                        data = json.loads(content)
                        logger.info(f"成功读取数据，共 {len(data)} 条新闻")
                        return data
                    else:
                        logger.info("数据文件为空，返回示例数据")
                        return self.get_sample_data()
            else:
                logger.warning("数据文件不存在，返回示例数据")
                return self.get_sample_data()
        except Exception as e:
            logger.error(f"读取新闻数据失败: {e}")
            # 返回示例数据作为后备
            return self.get_sample_data()

    def get_sample_data(self):
        # 返回示例数据
        sample_data = [
            {
                "title": "中国与美国在贸易问题上达成新的协议",
                "summary": "中美两国在贸易谈判中取得了重要进展，双方就关税问题达成了新的共识。",
                "link": "http://example.com/news1",
                "published": "2026-07-21",
                "source": "rss",
                "source_name": "xinhua",
                "source_display": "新华社",
                "scraped_at": "2026-07-21T10:00:00",
                "keyword_matches": 3,
                "source_cross_count": 1,
                "hot_score": 50,
                "category": "经济"
            },
            {
                "title": "人工智能技术取得重大突破",
                "summary": "最新的人工智能技术在多个领域实现了突破性进展。",
                "link": "http://example.com/news2",
                "published": "2026-07-21",
                "source": "rss",
                "source_name": "sina",
                "source_display": "新浪新闻",
                "scraped_at": "2026-07-21T10:00:00",
                "keyword_matches": 2,
                "source_cross_count": 1,
                "hot_score": 40,
                "category": "科技"
            }
        ]
        return sample_data

    def send_json_response(self, data):
        try:
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')  # 允许跨域
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            self.wfile.write(json_data.encode('utf-8'))
            logger.info("JSON响应发送成功")
        except Exception as e:
            logger.error(f"发送JSON响应失败: {e}")

    def send_404(self):
        self.send_response(404)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(b'Not Found')

# 启动服务器
if __name__ == "__main__":
    try:
        logger.info(f"正在启动服务器，端口: {PORT}")

        # 创建服务器
        with socketserver.TCPServer(('', PORT), NewsHandler) as httpd:
            logger.info(f"服务器启动成功")
            logger.info(f"访问地址: http://localhost:{PORT}/news_dashboard.html")

            # 启动服务器
            httpd.serve_forever()

    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        exit(1)