@echo off
setlocal enabledelayedexpansion

echo === mcp-recall-md local build ===
echo.

:: 1. Install dependencies
echo [1/4] Installing dependencies...
pip install -e . --quiet
if errorlevel 1 (
    echo ERROR: pip install failed
    pause
    exit /b 1
)
pip install pytest pyinstaller --quiet
if errorlevel 1 (
    echo ERROR: dev dependencies install failed
    pause
    exit /b 1
)

:: 2. Run tests
echo [2/4] Running tests...
python -m pytest tests/ -v
if errorlevel 1 (
    echo.
    echo ERROR: tests failed
    pause
    exit /b 1
)

:: 3. Build exe
echo [3/4] Building exe with PyInstaller...
pyinstaller mcp-recall-md.spec --noconfirm
if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)

:: 4. Verify output
echo [4/4] Verifying output...
if not exist "dist\mcp-recall-md.exe" (
    echo ERROR: dist\mcp-recall-md.exe not found
    pause
    exit /b 1
)

for %%F in ("dist\mcp-recall-md.exe") do set SIZE=%%~zF
set /a SIZE_MB=!SIZE! / 1048576
echo OK: dist\mcp-recall-md.exe  (!SIZE_MB! MB)

echo.
echo Build successful.
pause
