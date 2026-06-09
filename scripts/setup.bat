@echo off
chcp 65001 >nul
setlocal

:: ============================================================
::  HH-Research 首次环境初始化脚本 (Windows)
::  在新机器上克隆仓库后运行一次即可。
::  前提：Python 3.12+ 和 Node 18+ 已安装。
:: ============================================================

set "ROOT=%~dp0.."
set "BACKEND=%ROOT%\backend"
set "FRONTEND=%ROOT%\frontend"
set "PG_BIN=C:\Program Files\PostgreSQL\16\bin"
set PGPASSWORD=postgres

echo.
echo ============================================================
echo   HH-Research — 初始化环境
echo ============================================================

:: ── 1. 检查 Python ──────────────────────────────────────────
echo.
echo [1/5] 检查 Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [错误] 未找到 Python，请先安装 Python 3.12+
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('python --version') do echo   %%v ✓

:: ── 2. 后端虚拟环境 ──────────────────────────────────────────
echo.
echo [2/5] 初始化后端虚拟环境...
cd /d "%BACKEND%"
if not exist ".venv" (
    python -m venv .venv
    echo   虚拟环境创建完成
)
echo   安装 Python 依赖...
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
echo   后端依赖安装完成 ✓

:: ── 3. 前端依赖 ──────────────────────────────────────────────
echo.
echo [3/5] 安装前端依赖...
cd /d "%FRONTEND%"
if not exist "node_modules" (
    npm install --silent
) else (
    echo   node_modules 已存在，跳过
)
echo   前端依赖安装完成 ✓

:: ── 4. 数据库迁移 ────────────────────────────────────────────
echo.
echo [4/5] 运行数据库迁移...
"%PG_BIN%\psql.exe" -U postgres -h localhost -p 5432 -tAc "SELECT 1 FROM pg_database WHERE datname='ai_knowledge'" 2>nul | findstr "1" >nul
if %errorlevel% neq 0 (
    echo   创建数据库 ai_knowledge...
    "%PG_BIN%\createdb.exe" -U postgres -h localhost -p 5432 ai_knowledge
)
cd /d "%BACKEND%"
set DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_knowledge
set DATABASE_URL_SYNC=postgresql+psycopg2://postgres:postgres@localhost:5432/ai_knowledge
set DB_SSL_MODE=disable
.venv\Scripts\alembic.exe upgrade head
echo   迁移完成 ✓

:: ── 5. 示例数据 ──────────────────────────────────────────────
echo.
echo [5/5] 填充示例数据...
"%PG_BIN%\psql.exe" -U postgres -h localhost -p 5432 -d ai_knowledge -tAc "SELECT count(*) FROM entities" 2>nul | findstr "^0" >nul
if not %errorlevel% neq 0 (
    echo   数据库已有数据，跳过 seed
) else (
    .venv\Scripts\python.exe seed.py 2>nul
    echo   示例数据填充完成 ✓
)

:: ── 完成 ─────────────────────────────────────────────────────
echo.
echo ============================================================
echo   初始化完成！现在可以运行 start.bat 启动服务
echo ============================================================
echo.
pause
endlocal
