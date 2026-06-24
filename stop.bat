@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  FAKENEWS DETECTOR - DUNG TẤT CA SERVER
:: ============================================================

title FakeNews Detector - Stopping...

echo.
echo =====================================================
echo    FAKE NEWS DETECTOR - DUNG SERVER
echo =====================================================
echo.

:: --- Dung uvicorn (backend port 8000) ---
echo Dung Backend (uvicorn port 8000)...
for /f "tokens=5" %%p in ('netstat -aon 2^>nul ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    if not "%%p"=="" (
        taskkill /PID %%p /F >nul 2>&1
        echo Da dung PID %%p (port 8000).
    )
)

:: --- Dung Vite dev server (frontend port 5173) ---
echo Dung Frontend (vite port 5173)...
for /f "tokens=5" %%p in ('netstat -aon 2^>nul ^| findstr ":5173 " ^| findstr "LISTENING"') do (
    if not "%%p"=="" (
        taskkill /PID %%p /F >nul 2>&1
        echo Da dung PID %%p (port 5173).
    )
)

:: --- Dong cua so terminal backend/frontend ---
echo Dong cua so terminal backend/frontend...
taskkill /FI "WINDOWTITLE eq FakeNews BACKEND :8000" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq FakeNews FRONTEND :5173" /F >nul 2>&1

echo.
echo Tat ca server da dung.
echo.
pause
