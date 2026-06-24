@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: ============================================================
::  FAKENEWS DETECTOR — CHẠY TEST
::  Dùng pytest với virtual env trong backend\.venv
:: ============================================================

title FakeNews Detector — Tests

set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "VENV=%BACKEND%\.venv"

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║          FAKE NEWS DETECTOR — CHẠY TEST             ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

:: ─── Kiểm tra venv ────────────────────────────────────────
if not exist "%VENV%\Scripts\activate.bat" (
    echo  [LOI] Chưa có môi trường Python. Chạy setup.bat trước!
    pause
    exit /b 1
)

call "%VENV%\Scripts\activate.bat"

:: ─── Menu chọn loại test ──────────────────────────────────
echo  Chọn loại test muốn chạy:
echo.
echo   [1] Tất cả test
echo   [2] Chỉ test nhanh (preprocessing + model + dataset)
echo   [3] Test scraper
echo   [4] Test API endpoints
echo   [5] Test trainer
echo   [6] Tất cả + Coverage report
echo.
set /p "CHOICE=  Nhập số (mặc định 1): "
if "!CHOICE!"=="" set "CHOICE=1"

cd /d "%BACKEND%"

if "!CHOICE!"=="1" (
    echo.
    echo  Chạy tất cả test...
    echo  ─────────────────────────────────────────────────────
    python -m pytest -v --tb=short
)
if "!CHOICE!"=="2" (
    echo.
    echo  Chạy test nhanh...
    echo  ─────────────────────────────────────────────────────
    python -m pytest tests/test_preprocessing.py tests/test_model.py tests/test_dataset.py -v --tb=short
)
if "!CHOICE!"=="3" (
    echo.
    echo  Chạy test scraper...
    echo  ─────────────────────────────────────────────────────
    python -m pytest tests/test_scraper.py -v --tb=short
)
if "!CHOICE!"=="4" (
    echo.
    echo  Chạy test API...
    echo  ─────────────────────────────────────────────────────
    python -m pytest tests/test_api.py -v --tb=short
)
if "!CHOICE!"=="5" (
    echo.
    echo  Chạy test trainer...
    echo  ─────────────────────────────────────────────────────
    python -m pytest tests/test_trainer.py -v --tb=short
)
if "!CHOICE!"=="6" (
    echo.
    echo  Chạy tất cả test + coverage...
    echo  ─────────────────────────────────────────────────────
    python -m pytest --cov=src --cov=api --cov-report=term-missing --cov-report=html:logs/coverage -v --tb=short
    echo.
    echo  Coverage HTML đã lưu tại: backend\logs\coverage\index.html
    echo  Mở báo cáo...
    start "" "%BACKEND%\logs\coverage\index.html"
)

echo.
pause
