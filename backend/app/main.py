import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import config, repo, rules, status, tasks, upload


# 配置基础日志，所有路由和服务可复用同一日志格式。
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

# 创建 FastAPI 应用实例，统一挂载业务路由。
app = FastAPI(
    title="Asgis AI 工程规范分析助手",
    description="自动分析 Vue3 / TypeScript 项目并生成 AI Coding Rules。",
    version="0.1.0",
)

# 开发阶段允许前端本地访问，生产环境可改为指定域名。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由分层：上传、仓库解析、规则生成分别维护。
app.include_router(upload.router)
app.include_router(repo.router)
app.include_router(rules.router)
app.include_router(status.router)
app.include_router(tasks.router)
app.include_router(config.router)


@app.get("/health")
def health_check() -> dict:
    """健康检查接口，便于前端或部署平台探测服务状态。"""
    return {"status": "ok", "service": "asgis-backend"}
