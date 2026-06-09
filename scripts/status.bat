@echo off
chcp 65001 >nul

:: ============================================================
::  HH-Research 服务状态检查
:: ============================================================

echo.
echo ============================================================
echo   HH-Research — 服务状态
echo ============================================================
echo.

:: ── PostgreSQL ────────────────────────────────────────────────
echo [PostgreSQL 服务]
sc query postgresql-x64-16 | findstr /i "RUNNING" >nul 2>&1
if %errorlevel% equ 0 (
    echo   状态: 运行中 ✓  (localhost:5432)
) else (
    echo   状态: 未运行 ✗
)
echo.

:: ── 后端 ─────────────────────────────────────────────────────
echo [后端 FastAPI]
set "back_port="
for %%p in (8000 8001) do (
    curl -s -o nul -w "%%{http_code}" http://localhost:%%p/api/dashboard/stats 2>nul | findstr "200" >nul
    if not errorlevel 1 (
        set "back_port=%%p"
    )
)
if defined back_port (
    echo   状态: 运行中 ✓  (http://localhost:%back_port%)
    echo   API 文档:       http://localhost:%back_port%/docs
    for /f %%s in ('curl -s http://localhost:%back_port%/api/dashboard/stats 2^>nul') do echo   统计: %%s
) else (
    echo   状态: 未运行 ✗
)
echo.

:: ── 前端 ─────────────────────────────────────────────────────
echo [前端 Next.js]
curl -s -o nul -w "%%{http_code}" http://localhost:3000 2>nul | findstr "200 307 308" >nul
if %errorlevel% equ 0 (
    echo   状态: 运行中 ✓  (http://localhost:3000)
    if defined back_port (
        echo   知识图谱:       http://localhost:3000/graph
        echo   Wiki 搜索:      http://localhost:3000/wiki
        echo   仪表盘:         http://localhost:3000/dashboard
    )
) else (
    echo   状态: 未运行 ✗
)
echo.
echo ============================================================
echo.
pause
