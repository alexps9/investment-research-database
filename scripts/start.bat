@echo off
chcp 65001 >nul
setlocal

:: ============================================================
::  HH-Research 一键启动脚本 (Windows)
::  运行前提：PostgreSQL 16 已安装，前端依赖已用 npm install 安装
:: ============================================================

set "ROOT=%~dp0.."
set "BACKEND=%ROOT%\backend"
set "FRONTEND=%ROOT%\frontend"

echo.
echo ============================================================
echo   HH-Research — 启动中
echo ============================================================

:: ── 1. 检查 PostgreSQL 服务 ─────────────────────────────────
echo.
echo [1/3] 检查 PostgreSQL 服务...
sc query postgresql-x64-16 | findstr /i "RUNNING" >nul 2>&1
if %errorlevel% neq 0 (
    echo   PostgreSQL 未运行，尝试启动...
    net start postgresql-x64-16
    if %errorlevel% neq 0 (
        echo   [错误] 无法启动 PostgreSQL，请手动启动后重试。
        pause
        exit /b 1
    )
) else (
    echo   PostgreSQL 已在运行 ✓
)

:: ── 2. 检查 ai_knowledge 数据库 ──────────────────────────────
echo.
echo [2/3] 检查数据库 ai_knowledge...
set "PG_BIN=C:\Program Files\PostgreSQL\16\bin"
set PGPASSWORD=postgres
"%PG_BIN%\psql.exe" -U postgres -h localhost -p 5432 -tAc "SELECT 1 FROM pg_database WHERE datname='ai_knowledge'" 2>nul | findstr "1" >nul
if %errorlevel% neq 0 (
    echo   数据库不存在，正在创建...
    "%PG_BIN%\createdb.exe" -U postgres -h localhost -p 5432 ai_knowledge
    echo   运行数据库迁移...
    cd /d "%BACKEND%"
    set DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_knowledge
    set DATABASE_URL_SYNC=postgresql+psycopg2://postgres:postgres@localhost:5432/ai_knowledge
    set DB_SSL_MODE=disable
    .venv\Scripts\alembic.exe upgrade head
) else (
    echo   数据库 ai_knowledge 已存在 ✓
)

:: ── 3. 启动后端 ──────────────────────────────────────────────
echo.
echo [3/3] 启动服务...
echo   启动后端 (http://localhost:8001) ...

:: 检查 8000 是否被占用，选择端口
netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    set "BACKEND_PORT=8001"
    echo   端口 8000 被占用，使用 8001
) else (
    set "BACKEND_PORT=8000"
)

start "HH-Research Backend" cmd /k "cd /d %BACKEND% && set DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_knowledge && set DATABASE_URL_SYNC=postgresql+psycopg2://postgres:postgres@localhost:5432/ai_knowledge && set DB_SSL_MODE=disable && .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port %BACKEND_PORT% --reload"

:: 等待后端就绪
echo   等待后端启动...
:wait_backend
timeout /t 2 /nobreak >nul
curl -s -o nul -w "%%{http_code}" http://localhost:%BACKEND_PORT%/api/dashboard/stats 2>nul | findstr "200" >nul
if %errorlevel% neq 0 goto wait_backend
echo   后端已就绪 ✓

:: ── 4. 启动前端 ──────────────────────────────────────────────
echo   启动前端 (http://localhost:3000) ...
start "HH-Research Frontend" cmd /k "cd /d %FRONTEND% && set NEXT_PUBLIC_API_URL=http://localhost:%BACKEND_PORT% && npm run dev"

:: ── 完成提示 ─────────────────────────────────────────────────
echo.
echo ============================================================
echo   启动完成！
echo.
echo   前端界面：  http://localhost:3000
echo   后端 API：  http://localhost:%BACKEND_PORT%
echo   API 文档：  http://localhost:%BACKEND_PORT%/docs
echo.
echo   知识图谱：  http://localhost:3000/graph
echo   Wiki 搜索： http://localhost:3000/wiki
echo ============================================================
echo.

:: 自动打开浏览器（等前端就绪）
echo 等待前端就绪后自动打开浏览器...
:wait_frontend
timeout /t 2 /nobreak >nul
curl -s -o nul -w "%%{http_code}" http://localhost:3000 2>nul | findstr "200 307 308" >nul
if %errorlevel% neq 0 goto wait_frontend
start http://localhost:3000/graph

endlocal
