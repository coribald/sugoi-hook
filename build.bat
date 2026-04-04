@echo off
echo ========================================
echo Building Single EXE with Nuitka (Fixed)
echo ========================================
echo.

set "PIP_CACHE_DIR=%CD%\.pip-cache"
set "NUITKA_CACHE_DIR=%CD%\.nuitka-cache"
set "OUTPUT_DIR=SugoiHook_builds"
set "PRESERVE_DIR=.build-preserve\release"

echo Preserving runtime *_config.json files from %OUTPUT_DIR%...
if exist "%PRESERVE_DIR%" rmdir /s /q "%PRESERVE_DIR%"
mkdir "%PRESERVE_DIR%" >nul 2>&1
if exist "%OUTPUT_DIR%\*_config.json" copy /y "%OUTPUT_DIR%\*_config.json" "%PRESERVE_DIR%\" >nul

echo Cleaning previous release build artifacts...
if exist "%OUTPUT_DIR%" rmdir /s /q "%OUTPUT_DIR%"

REM Check if Nuitka and onefile compression support are installed
python -c "import nuitka, zstandard" 2>nul
if errorlevel 1 (
    echo Nuitka and/or zstandard not found. Installing...
    python -m pip install nuitka zstandard
    echo.
)

echo Starting Nuitka compilation...
echo This creates a SINGLE EXE file with ALL runtime assets bundled
echo May take 10-15 minutes on first run...
echo.

REM Build with Nuitka - Single file mode with raw runtime assets included
python -m nuitka ^
    --onefile ^
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
    --windows-console-mode=disable ^
    --force-stdout-spec={PROGRAM_BASE}.stdout.txt ^
    --force-stderr-spec={PROGRAM_BASE}.stderr.txt ^
    --output-dir=%OUTPUT_DIR% ^
    --company-name="Sugoi Toolkit Inc." ^
    --product-name="Sugoi Hook" ^
    --file-version=2.0.1 ^
    --product-version=2.0.1 ^
    --file-description="Modern Hooking Interface" ^
    --output-filename=SugoiHook.exe ^
    SugoiHook_gui.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo Build Failed!
    echo ========================================
    echo.
    pause
    exit /b 1
)

if exist "%PRESERVE_DIR%\*_config.json" (
    echo Restoring preserved runtime config files...
    copy /y "%PRESERVE_DIR%\*_config.json" "%OUTPUT_DIR%\" >nul
)

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Executable created: %OUTPUT_DIR%\SugoiHook.exe
echo.
pause
