@echo off
REM ============================================================================
REM YouTube Audio Archiver - Windows Launcher
REM ============================================================================
REM Double-click this file to start the downloader and open the web dashboard
REM ============================================================================

echo.
echo ============================================================
echo   YouTube Audio Archiver
echo   Starting server and opening dashboard...
echo ============================================================
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -3.12 -m venv venv
)

REM Install required packages if needed
echo Checking dependencies...
venv\Scripts\pip install -q flask yt-dlp ffmpeg-python imageio-ffmpeg 2>nul

echo.
echo Starting server on http://localhost:8000
echo Opening browser...
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the Flask server and open browser
start "" http://localhost:8000
venv\Scripts\python.exe app.py

pause
