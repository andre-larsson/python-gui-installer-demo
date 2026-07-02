# Simple GUI Installer Demo

This repository is an educational demo, not a production application. It shows the basic shape of a distributable Python desktop app with a Windows installer.

The app demonstrates:

- `tkinter` / `ttk` GUI
- a background worker thread that does not block the UI
- local JSON settings storage
- PyInstaller build script
- Inno Setup installer script
- GitHub Actions workflow for building the installer on Windows

The app itself only uses the Python standard library. PyInstaller and Inno Setup are only needed when building the Windows executable and installer.

## Demo Scope

This project is intentionally small so the packaging flow is easy to inspect:

- it is meant for learning Python desktop packaging
- it is not code signed
- it does not include auto-updates
- it does not include crash reporting or telemetry
- it does not try to be a complete application template

Use it as a starting point for understanding the moving parts, then adapt the structure for a real app.

## Project Layout

```text
python-gui-installer-demo/
  app/
    main.py                  # desktop GUI app
  installer/
    SimpleGuiDemo.iss        # Inno Setup installer script
  scripts/
    build_windows.bat        # build exe, then installer if ISCC is available
  requirements-build.txt     # build-time Python dependencies
```

## Run From Source

From this directory:

```bat
py app\main.py
```

On macOS/Linux:

```sh
python3 app/main.py
```

## Build The Windows App

Run this on Windows, not Linux/macOS. PyInstaller packages for the OS it is running on.

```bat
scripts\build_windows.bat
```

The script will:

1. create `.venv` if needed
2. install PyInstaller
3. build `dist\SimpleGuiDemo\SimpleGuiDemo.exe`
4. run Inno Setup Compiler if `ISCC.exe` is on your `PATH`

If Inno Setup is not installed or not on `PATH`, open `installer\SimpleGuiDemo.iss` in the Inno Setup Compiler GUI and build it manually after PyInstaller finishes.

## Install Output

After a successful Inno Setup build, the installer will be placed here:

```text
dist\installer\SimpleGuiDemoSetup.exe
```

That installer includes the PyInstaller-built app, so the end user does not need Python installed.

## Build On GitHub Actions

This project includes a Windows workflow at:

```text
.github/workflows/windows-installer.yml
```

Push the project to GitHub, then run **Actions > Build Windows Installer > Run workflow**. The workflow builds on `windows-latest`, installs Inno Setup, runs `scripts\build_windows.bat`, and uploads two artifacts:

- `SimpleGuiDemoSetup`: the Inno Setup installer
- `SimpleGuiDemo-Windows`: the unpacked PyInstaller app folder

If this folder is part of a larger repository, the `.github` directory must live at that repository's root for GitHub Actions to discover it.
