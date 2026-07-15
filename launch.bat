@echo off
setlocal EnableDelayedExpansion
cd /d %~dp0

echo ============================================
echo   Spotify Concert Finder
echo ============================================
echo.

:: ---------------------------------------------------------------------------
:: Step 1: Check if Python is installed
:: ---------------------------------------------------------------------------

python --version >nul 2>&1
if %errorlevel% == 0 (
    goto :check_venv
)

:: Python not found — check if we can use the known per-user install path
set PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
if exist "%PYTHON_EXE%" (
    echo Found Python at %PYTHON_EXE%.
    goto :check_venv_explicit
)

:: ---------------------------------------------------------------------------
:: Step 2: Auto-install Python via curl
:: ---------------------------------------------------------------------------

echo Python not found. Starting automatic installation...
echo.

:: Check curl is available
curl --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] curl is not available on this system.
    echo Please install Python manually from:
    echo   https://www.python.org/downloads/
    echo Make sure to tick "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: Download the installer
set INSTALLER=%TEMP%\python_installer.exe
set PYTHON_URL=https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe

echo Downloading Python 3.12.10 installer...
echo Please wait — this may take a moment depending on your connection.
echo.

curl -L --progress-bar -o "%INSTALLER%" "%PYTHON_URL%"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Download failed. Please check your internet connection.
    echo You can also install Python manually from:
    echo   https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo.
echo Download complete.
echo.
echo Installing Python 3.12.10 (per-user, no admin required)...
echo This may take a minute — please wait...
echo.

"%INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation failed.
    echo Please install Python manually from:
    echo   https://www.python.org/downloads/
    echo Make sure to tick "Add Python to PATH" during installation.
    echo.
    del /f /q "%INSTALLER%" >nul 2>&1
    pause
    exit /b 1
)

:: Clean up installer
del /f /q "%INSTALLER%" >nul 2>&1

echo Python installed successfully.
echo.

:: Use explicit path since PATH won't update in the current session
set PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python was installed but could not be found at the expected location.
    echo Please restart this script, or install Python manually from:
    echo   https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

goto :check_venv_explicit

:: ---------------------------------------------------------------------------
:: Step 3: Check / create venv (using PATH python)
:: ---------------------------------------------------------------------------

:check_venv
set PYTHON_EXE=python

:check_venv_explicit
if not exist venv (
    echo Setting up virtual environment...
    "%PYTHON_EXE%" -m venv venv
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Failed to create virtual environment.
        echo Make sure python3-venv or equivalent is available.
        echo Try running: python -m pip install virtualenv
        echo.
        pause
        exit /b 1
    )
    echo Virtual environment created.
    echo.
)

:: ---------------------------------------------------------------------------
:: Step 4: Activate venv
:: ---------------------------------------------------------------------------

call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

:: ---------------------------------------------------------------------------
:: Step 5: Install / update dependencies
:: ---------------------------------------------------------------------------

echo Checking dependencies...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install dependencies.
    echo Try running: pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)
echo Dependencies up to date.
echo.

:: ---------------------------------------------------------------------------
:: Step 6: Launch the app
:: ---------------------------------------------------------------------------

echo Starting Spotify Concert Finder...
echo.
python main.py

pause
