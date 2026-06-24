@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  FAKENEWS DETECTOR - KHOI DONG
::  Bat Backend (FastAPI) + Frontend (Vite) cung luc
::  Backend : http://localhost:8000
::  Frontend: http://localhost:5173
:: ============================================================

title FakeNews Detector - Starting...

set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "FRONTEND=%ROOT%frontend"
set "VENV=%BACKEND%\.venv"

echo.
echo =====================================================
echo    FAKE NEWS DETECTOR - KHOI DONG
echo =====================================================
echo.

:: --- Kiem tra da setup chua ---
if not exist "%VENV%\Scripts\activate.bat" (
    echo [CANH BAO] Chua co moi truong Python!
    echo Dang chay setup.bat tu dong...
    echo.
    call "%ROOT%setup.bat"
    if errorlevel 1 exit /b 1
)

if not exist "%FRONTEND%\node_modules" (
    echo [CANH BAO] Chua co node_modules!
    echo Dang chay setup.bat tu dong...
    echo.
    call "%ROOT%setup.bat"
    if errorlevel 1 exit /b 1
)

:: --- Khoi dong Backend ---
echo [1/2] Khoi dong Backend (FastAPI + PhoBERT)...
echo       http://localhost:8000
echo       http://localhost:8000/docs  (Swagger UI)
echo.

start "FakeNews BACKEND :8000" cmd /k ^
    "title FakeNews BACKEND :8000 && cd /d "%BACKEND%" && call .venv\Scripts\activate.bat && echo. && echo Backend dang chay tai http://localhost:8000 && echo Swagger UI: http://localhost:8000/docs && echo Nhan Ctrl+C de dung. && echo. && uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload"

:: Doi backend khoi dong truoc
echo Doi backend khoi dong (5 giay)...
timeout /t 5 /nobreak >nul

:: --- Khoi dong Frontend ---
echo [2/2] Khoi dong Frontend (React + Vite)...
echo       http://localhost:5173
echo.

start "FakeNews FRONTEND :5173" cmd /k ^
    "title FakeNews FRONTEND :5173 && cd /d "%FRONTEND%" && echo. && echo Frontend dang chay tai http://localhost:5173 && echo Nhan Ctrl+C de dung. && echo. && npm run dev"

:: Doi frontend khoi dong
timeout /t 4 /nobreak >nul

:: --- Mo trinh duyet ---
echo Mo trinh duyet...
start "" "http://localhost:5173"

:: --- Thong tin tom tat ---
echo.
echo =====================================================
echo  Ung dung dang chay:
echo.
echo   Frontend : http://localhost:5173
echo   Backend  : http://localhost:8000
echo   Swagger  : http://localhost:8000/docs
echo.
echo  Dong 2 cua so terminal de dung.
echo  Hoac chay stop.bat de dung tat ca.
echo =====================================================
echo.
echo Nhan phim bat ky de dong cua so nay...
pause >nul
