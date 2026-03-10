@echo off
REM YouTube Video Links Downloader Launcher
REM This script runs the download_videos.py script

echo ==============================================
echo YouTube Video Links Downloader
echo ==============================================
echo.
echo Options:
echo   1. Download videos (normal mode)
echo   2. Download videos (test mode - no actual download)
echo   3. Show download status
echo   4. Retry failed downloads
echo   5. Force re-download all videos
echo.
set /p choice="Choose an option (1-5): "

if "%choice%"=="1" goto download
if "%choice%"=="2" goto test
if "%choice%"=="3" goto status
if "%choice%"=="4" goto retry
if "%choice%"=="5" goto force

:download
echo.
echo Starting download...
python download_videos.py
goto end

:test
echo.
echo Running in test mode...
python download_videos.py --test
goto end

:status
echo.
echo Showing status...
python download_videos.py --status
goto end

:retry
echo.
echo Retrying failed downloads...
python download_videos.py --retry-failed
goto end

:force
echo.
echo Force re-downloading all videos...
python download_videos.py --force
goto end

:end
echo.
pause
