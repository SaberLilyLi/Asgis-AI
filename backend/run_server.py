import uvicorn


# 本地开发启动脚本，便于 Windows 后台进程稳定启动。
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, log_level="info")

