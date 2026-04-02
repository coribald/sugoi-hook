@echo off
echo ========================================
echo Building Standalone Debug EXE
echo ========================================
echo.

set "PIP_CACHE_DIR=%CD%\.pip-cache"
set "NUITKA_CACHE_DIR=%CD%\.nuitka-cache"

python -c "import nuitka, zstandard" 2>nul
if errorlevel 1 (
    echo Nuitka and/or zstandard not found. Installing...
    python -m pip install nuitka zstandard
    echo.
)

echo Starting standalone debug build...
echo.

python -m nuitka ^
    --mode=standalone ^
    --include-raw-dir=textractor_builds=textractor_builds ^
    --include-raw-dir=luna_builds=luna_builds ^
    --include-raw-dir=plugins=plugins ^
    --include-raw-dir=Translator=Translator ^
    --include-data-files=logo.webp=logo.webp ^
    --enable-plugin=tk-inter ^
    --include-module=tkinter.font ^
    --include-package=pystray ^
    --include-package=PIL ^
    --include-package=psutil ^
    --include-package=requests ^
    --include-package=bs4 ^
    --include-package=win32gui ^
    --include-package=win32ui ^
    --include-package=win32con ^
    --include-package=win32api ^
    --include-package=win32process ^
    --include-package=websocket_server ^
    --follow-imports ^
    --assume-yes-for-downloads ^
    --windows-console-mode=attach ^
    --output-dir=SugoiHook_debug_builds ^
    --company-name="Sugoi Toolkit Inc." ^
    --product-name="Sugoi Hook" ^
    --file-version=2.0.1 ^
    --product-version=2.0.1 ^
    --file-description="Modern Hooking Interface (Debug)" ^
    --output-filename=SugoiHook_debug.exe ^
    SugoiHook_gui.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo Debug Build Failed!
    echo ========================================
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Debug Build Complete!
echo ========================================
echo.
echo Executable created: SugoiHook_debug_builds\SugoiHook_debug.exe
pause




