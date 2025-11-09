@echo off
REM Setup script for Zero-Knowledge Identity System (Windows)
REM Creates a virtual environment and installs dependencies

echo 🔧 Setting up Zero-Knowledge Identity System Python environment...

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    echo Please install Python 3.11 or later from https://www.python.org/
    exit /b 1
)

echo ✅ Python found: 
python --version

REM Create virtual environment
if exist .venv (
    echo 📦 Virtual environment already exists at .venv
    set /p RECREATE="Do you want to recreate it? (y/N): "
    if /i "%RECREATE%"=="y" (
        echo 🗑️  Removing existing virtual environment...
        rmdir /s /q .venv
    ) else (
        echo Using existing virtual environment.
        goto activate
    )
)

echo 📦 Creating virtual environment...
python -m venv .venv

:activate
REM Activate virtual environment
echo 🔌 Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

REM Install production dependencies
echo 📥 Installing production dependencies...
pip install -r requirements.txt

REM Ask about development dependencies
set /p INSTALL_DEV="Install development dependencies (pytest, hypothesis)? (y/N): "
if /i "%INSTALL_DEV%"=="y" (
    echo 📥 Installing development dependencies...
    pip install -r requirements-dev.txt
)

REM Install package in editable mode
echo 📦 Installing zkidentity package in editable mode...
pip install -e .

echo.
echo ✅ Setup complete!
echo.
echo To activate the virtual environment in the future, run:
echo   .venv\Scripts\activate
echo.
echo To use the CLI:
echo   zkidentity --help
echo.
echo Or use Python directly:
echo   python -m cli.main --help
echo.

pause

