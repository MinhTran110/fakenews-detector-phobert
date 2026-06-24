@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  FAKENEWS DETECTOR - SETUP (Chi can chay 1 lan)
::  Tao virtual env, cai Python packages, cai npm packages
:: ============================================================

title FakeNews Detector - Setup

set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "FRONTEND=%ROOT%frontend"
set "VENV=%BACKEND%\.venv"

echo.
echo =====================================================
echo    FAKE NEWS DETECTOR - CAI DAT LAN DAU
echo    PhoBERT + FastAPI + React
echo =====================================================
echo.

:: --- Kiem tra Python ---
echo [1/5] Kiem tra Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [LOI] Khong tim thay Python!
    echo Tai Python tai: https://www.python.org/downloads/
    echo Luu y: Tick "Add Python to PATH" khi cai.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo Da co: %%v
echo.

:: --- Kiem tra Node / npm ---
echo [2/5] Kiem tra Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    :: Thu tim trong duong dan mac dinh xem co khong
    if exist "C:\Program Files\nodejs\node.exe" (
        set "PATH=%PATH%;C:\Program Files\nodejs"
        echo Da tu dong sua duong dan Node.js
    ) else (
        echo.
        echo =====================================================
        echo [LOI] Khong tim thay Node.js hoac npm!
        echo.
        echo Mac du ban da tai, nhung co the ban chua khoi dong lai
        echo may tinh hoac cua so CMD de cap nhat duong dan.
        echo.
        echo Vui long:
        echo 1. Dong cua so CMD nay lai.
        echo 2. Mo lai file setup.bat nay tu thu muc.
        echo 3. Neu van bi, hay restart may tinh de Windows nhan Node.js.
        echo =====================================================
        pause
        exit /b 1
    )
)
for /f "tokens=*" %%v in ('node --version 2^>^&1') do echo Node.js: %%v
for /f "tokens=*" %%v in ('npm --version 2^>^&1') do echo npm:     %%v
echo.

:: --- Tao Virtual Environment Python ---
echo [3/5] Tao moi truong Python ao (venv)...
if exist "%VENV%" (
    echo Da co .venv, bo qua tao moi.
) else (
    python -m venv "%VENV%"
    if errorlevel 1 (
        echo [LOI] Khong tao duoc venv!
        pause
        exit /b 1
    )
    echo Da tao: backend\.venv
)
echo.

:: --- Cai Python packages ---
echo [4/5] Cai dat Python packages (co the mat vai phut)...
call "%VENV%\Scripts\activate.bat"
pip install -r "%BACKEND%\requirements.txt" --quiet --disable-pip-version-check
if errorlevel 1 (
    echo [LOI] pip install that bai!
    echo Thu chay lai hoac kiem tra ket noi mang.
    pause
    exit /b 1
)
echo Da cai xong Python packages.
echo.

:: --- Cai npm packages ---
echo [5/5] Cai dat npm packages cho Frontend...
if exist "%FRONTEND%\node_modules" (
    echo Da co node_modules, bo qua.
) else (
    pushd "%FRONTEND%"
    npm install --silent
    if errorlevel 1 (
        echo [LOI] npm install that bai!
        popd
        pause
        exit /b 1
    )
    popd
    echo Da cai xong npm packages.
)
echo.

:: --- Tao .env.local neu chua co ---
if not exist "%FRONTEND%\.env.local" (
    copy "%FRONTEND%\.env.example" "%FRONTEND%\.env.local" >nul
    echo Da tao frontend\.env.local
)

:: --- Xong ---
echo.
echo =====================================================
echo    CAI DAT HOAN TAT!
echo    Chay start.bat de khoi dong ung dung.
echo =====================================================
echo.
pause
