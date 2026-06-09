@echo off
chcp 65001 >nul

:: ============================================================
::  HH-Research 一键停止脚本 (Windows)
:: ============================================================

echo.
echo ============================================================
echo   HH-Research — 停止服务
echo ============================================================
echo.

:: ── 停止后端（占用 8000 或 8001 的 Python uvicorn）────────────
echo [1/2] 停止后端...
set "stopped_back=0"
for %%p in (8000 8001) do (
    for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":%%p " ^| findstr "LISTENING"') do (
        tasklist /fi "PID eq %%i" 2>nul | findstr /i "python" >nul
        if not errorlevel 1 (
            taskkill /PID %%i /T /F >nul 2>&1
            echo   已停止端口 %%p 上的后端进程 (PID %%i) ✓
            set "stopped_back=1"
        )
    )
)
if "%stopped_back%"=="0" echo   未发现正在运行的后端进程

:: ── 停止前端（占用 3000 的 Node）─────────────────────────────
echo.
echo [2/2] 停止前端...
set "stopped_front=0"
for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":3000 " ^| findstr "LISTENING"') do (
    tasklist /fi "PID eq %%i" 2>nul | findstr /i "node" >nul
    if not errorlevel 1 (
        taskkill /PID %%i /T /F >nul 2>&1
        echo   已停止端口 3000 上的前端进程 (PID %%i) ✓
        set "stopped_front=1"
    )
)
if "%stopped_front%"=="0" echo   未发现正在运行的前端进程

echo.
echo ============================================================
echo   服务已全部停止
echo   (PostgreSQL 系统服务保持运行，如需停止请运行 stop-pg.bat)
echo ============================================================
echo.
pause
