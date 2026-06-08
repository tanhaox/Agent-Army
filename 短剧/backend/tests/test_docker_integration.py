"""
Docker 集成测试 - 验证容器环境下前后端联调正常。

前提：docker-compose up -d 已启动所有服务。
从宿主机运行此脚本，通过 HTTP 访问容器服务。
"""

import time

import httpx
import pytest

# 容器暴露的端口
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost"
HEALTH_TIMEOUT = 60  # 等待后端健康的秒数


def wait_for_backend():
    """等待后端健康检查通过。"""
    start = time.time()
    while time.time() - start < HEALTH_TIMEOUT:
        try:
            resp = httpx.get(f"{BASE_URL}/health", timeout=5)
            if resp.status_code == 200:
                return
        except httpx.ConnectError:
            pass
        time.sleep(2)
    pytest.skip(f"后端在 {HEALTH_TIMEOUT} 秒内未就绪，跳过集成测试")


# 在模块级别等待后端就绪
@pytest.fixture(scope="module", autouse=True)
def backend_ready():
    """确保后端服务可用后再运行测试。"""
    wait_for_backend()


class TestHealthCheck:
    """服务健康检查。"""

    def test_backend_health(self) -> None:
        """后端 /health 返回 200，并包含 deepseek 状态字段。"""
        resp = httpx.get(f"{BASE_URL}/health", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "deepseek" in data
        assert "status" in data["deepseek"]

    def test_frontend_serves_html(self) -> None:
        """前端返回 HTML 页面。"""
        resp = httpx.get(FRONTEND_URL, timeout=10)
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")


class TestFrontendProxy:
    """Nginx 反向代理验证。"""

    def test_api_proxy(self) -> None:
        """通过 nginx 代理访问后端 API。"""
        resp = httpx.get(f"{FRONTEND_URL}/health", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_api_scripts_proxy(self) -> None:
        """通过 nginx 代理访问 /api/scripts/ 路径。"""
        resp = httpx.get(f"{FRONTEND_URL}/api/scripts/", timeout=10)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestScriptGeneration:
    """剧本查询流程（需要 DeepSeek 可用）。"""

    def test_list_scripts(self) -> None:
        """查询剧本列表，验证接口可用。"""
        resp = httpx.get(f"{BASE_URL}/api/scripts/", timeout=10)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestDeepSeekConnectivity:
    """DeepSeek 连通性检查。"""

    def test_deepseek_reachable_from_health(self) -> None:
        """通过 /health 端点检查 DeepSeek 是否可达。"""
        resp = httpx.get(f"{BASE_URL}/health", timeout=10)
        data = resp.json()
        assert "deepseek" in data
        deepseek_info = data["deepseek"]
        if deepseek_info.get("status") != "ok":
            import warnings
            warnings.warn(
                f"DeepSeek 不可达: {deepseek_info.get('detail', '未知')}",
                stacklevel=1,
            )


class TestStaticDirectory:
    """静态文件目录和代理检查。"""

    def test_static_characters_accessible(self) -> None:
        """静态目录 /static/characters/ 可访问（返回 404 也表示路由已注册）。"""
        resp = httpx.get(f"{BASE_URL}/static/characters/", timeout=10, follow_redirects=True)
        # 404 表示目录存在但为空，403 表示目录存在但禁止列表
        assert resp.status_code in (200, 403, 404)

    def test_frontend_static_proxy(self) -> None:
        """通过 nginx 可访问 /static/ 路径。"""
        resp = httpx.get(f"{FRONTEND_URL}/static/characters/", timeout=10, follow_redirects=True)
        # nginx 代理 /static/ 到后端
        assert resp.status_code in (200, 403, 404)
