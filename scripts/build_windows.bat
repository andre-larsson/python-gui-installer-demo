@echo off
setlocal

cd /d "%~dp0\.."

if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
)

call ".venv\Scripts\activate.bat"

python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onedir ^
    --windowed ^
    --name SimpleGuiDemo ^
    app\main.py

if errorlevel 1 (
    echo PyInstaller build failed.
    exit /b 1
)

where ISCC >nul 2>nul
if errorlevel 1 (
    echo.
    echo PyInstaller finished: dist\SimpleGuiDemo\SimpleGuiDemo.exe
    echo Inno Setup Compiler was not found on PATH.
    echo Open installer\SimpleGuiDemo.iss in Inno Setup Compiler to build the installer.
    exit /b 0
)

ISCC installer\SimpleGuiDemo.iss

if errorlevel 1 (
    echo Inno Setup build failed.
    exit /b 1
)

echo.
echo Done: dist\installer\SimpleGuiDemoSetup.exe
