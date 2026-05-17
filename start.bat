@echo off
title Plagiarism Checker

cd /d "%~dp0"

echo ============================================
echo   Academic Plagiarism Checker
echo ============================================
echo(

:: Skip Streamlit first-launch email prompt
if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
    echo [general] > "%USERPROFILE%\.streamlit\credentials.toml"
    echo email = "" >> "%USERPROFILE%\.streamlit\credentials.toml"
)

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.11+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Install packages on first run
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo [INFO] First run - installing required packages...
    echo(
    pip install -r requirements.txt
    if errorlevel 1 (
        echo(
        echo [ERROR] Installation failed. Check your internet connection.
        pause
        exit /b 1
    )
    echo(
    echo [OK] Packages installed successfully.
    echo(
)

echo Starting server... Browser will open at http://localhost:8501
echo Close this window to stop the server.
echo ============================================
echo(

streamlit run app.py --browser.gatherUsageStats false

pause
