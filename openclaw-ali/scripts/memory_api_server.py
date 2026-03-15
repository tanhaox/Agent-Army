#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenClaw 记忆API服务器
提供持久化记忆存储和检索功能
端口: 18888
"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import duckdb
from datetime import datetime
import uvicorn
import logging
from pathlib import Path

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/.openclaw/workspace/logs/memory_api.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 数据库路径
DB_PATH = Path('/root/.openclaw/workspace/data/memory.duckdb')
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# 创建FastAPI应用
app = FastAPI(
    title="OpenClaw Memory API",
    description="持久化记忆存储和检索服务",
    version="1.0.0"
)

# 数据模型
class RememberRequest(BaseModel):
    content: str
    category: str
    importance: int = 80
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None

class RecallRequest(BaseModel):
    category: Optional[str] = None
    limit: int = 10
    min_importance: int = 0

class SearchRequest(BaseModel):
    query: str
    limit: int = 10

class MemoryResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

# 初始化数据库
def init_db():
    """初始化数据库表"""
    conn = duckdb.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY,
            content TEXT,
            category VARCHAR(100),
            importance INTEGER DEFAULT 80,
            tags VARCHAR(500),
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_category ON memories(category);
        CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance);
        CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at);
    """)
    conn.close()
    logger.info(f"数据库初始化完成: {DB_PATH}")

# API端点
@app.get("/")
async def root():
    """健康检查"""
    return {
        "service": "OpenClaw Memory API",
        "status": "running",
        "version": "1.0.0",
        "database": str(DB_PATH)
    }

@app.get("/health")
async def health():
    """健康检查"""
    try:
        conn = duckdb.connect(str(DB_PATH))
        count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        conn.close()
        return {
            "status": "healthy",
            "memory_count": count,
            "database": str(DB_PATH)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/memory/remember", response_model=MemoryResponse)
async def remember(request: RememberRequest):
    """存储记忆"""
    try:
        conn = duckdb.connect(str(DB_PATH))

        # 生成新ID
        result = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM memories").fetchone()
        memory_id = result[0] if result else 1

        # 将tags和metadata转换为JSON字符串
        tags_str = ','.join(request.tags) if request.tags else None
        metadata_str = str(request.metadata) if request.metadata else None

        conn.execute("""
            INSERT INTO memories (id, content, category, importance, tags, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (memory_id, request.content, request.category, request.importance, tags_str, metadata_str))

        conn.close()

        logger.info(f"记忆已存储: ID={memory_id}, category={request.category}")

        return MemoryResponse(
            success=True,
            message=f"记忆已存储，ID: {memory_id}",
            data={"id": memory_id}
        )

    except Exception as e:
        logger.error(f"存储记忆失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/memory/recall", response_model=MemoryResponse)
async def recall(request: RecallRequest):
    """检索记忆"""
    try:
        conn = duckdb.connect(str(DB_PATH))

        # 构建查询
        query = "SELECT * FROM memories WHERE 1=1"
        params = []

        if request.category:
            query += " AND category = ?"
            params.append(request.category)

        if request.min_importance > 0:
            query += " AND importance >= ?"
            params.append(request.min_importance)

        query += " ORDER BY importance DESC, created_at DESC LIMIT ?"
        params.append(request.limit)

        results = conn.execute(query, params).fetchall()
        conn.close()

        memories = []
        for row in results:
            memories.append({
                "id": row[0],
                "content": row[1],
                "category": row[2],
                "importance": row[3],
                "tags": row[4].split(',') if row[4] else [],
                "created_at": str(row[6])
            })

        logger.info(f"检索到 {len(memories)} 条记忆")

        return MemoryResponse(
            success=True,
            message=f"检索到 {len(memories)} 条记忆",
            data={"memories": memories}
        )

    except Exception as e:
        logger.error(f"检索记忆失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/memory/search", response_model=MemoryResponse)
async def search(request: SearchRequest):
    """搜索记忆"""
    try:
        conn = duckdb.connect(str(DB_PATH))

        # 全文搜索
        query = """
            SELECT * FROM memories
            WHERE content LIKE ? OR category LIKE ?
            ORDER BY importance DESC, created_at DESC
            LIMIT ?
        """
        search_pattern = f"%{request.query}%"
        results = conn.execute(query, (search_pattern, search_pattern, request.limit)).fetchall()
        conn.close()

        memories = []
        for row in results:
            memories.append({
                "id": row[0],
                "content": row[1],
                "category": row[2],
                "importance": row[3],
                "tags": row[4].split(',') if row[4] else [],
                "created_at": str(row[6])
            })

        logger.info(f"搜索到 {len(memories)} 条记忆")

        return MemoryResponse(
            success=True,
            message=f"搜索到 {len(memories)} 条记忆",
            data={"memories": memories}
        )

    except Exception as e:
        logger.error(f"搜索记忆失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memory/stats")
async def stats():
    """获取记忆统计"""
    try:
        conn = duckdb.connect(str(DB_PATH))

        total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        by_category = conn.execute("""
            SELECT category, COUNT(*) as count
            FROM memories
            GROUP BY category
            ORDER BY count DESC
        """).fetchall()

        conn.close()

        stats_data = {
            "total": total,
            "by_category": {cat: cnt for cat, cnt in by_category}
        }

        return MemoryResponse(
            success=True,
            message="统计完成",
            data=stats_data
        )

    except Exception as e:
        logger.error(f"获取统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def main():
    """启动服务器"""
    logger.info("="*60)
    logger.info(" OpenClaw 记忆API服务器")
    logger.info("="*60)
    logger.info(f" 端口: 18888")
    logger.info(f" 数据库: {DB_PATH}")
    logger.info("="*60)
    logger.info("")

    # 初始化数据库
    init_db()

    # 启动服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=18888,
        log_level="info"
    )

if __name__ == '__main__':
    main()
