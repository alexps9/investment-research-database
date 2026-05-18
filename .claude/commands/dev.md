启动开发环境（后端 + 前端）。

执行步骤：
1. 检查端口 8000 和 3000 是否被占用，如果是则先 kill
2. 在 `backend/` 目录启动：`python -m uvicorn app.main:app --reload --port 8000`（后台运行）
3. 在 `frontend/` 目录启动：`npm run dev`（后台运行）
4. 等待两个服务就绪，用 curl 验证健康检查
5. 报告两个服务的状态
