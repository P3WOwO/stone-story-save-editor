@echo off
setlocal
cd /d "%~dp0"
title Stone Story RPG Save Editor

echo ===============================================
echo   Stone Story RPG Save Editor
echo ===============================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON=py -3"
) else (
    set "PYTHON=python"
)

if not exist ".venv\Scripts\python.exe" (
    echo First start: preparing the program ^(needs internet, takes ~1 minute^)...
    %PYTHON% -m venv .venv
    if errorlevel 1 goto :nopython
)

".venv\Scripts\python.exe" -m pip install -q -r requirements.txt
if errorlevel 1 goto :error

start "" ".venv\Scripts\pythonw.exe" -m stone_story_editor
goto :eof

:nopython
echo.
echo Python was not found. Install Python 3.10 or newer from https://www.python.org/downloads/
echo IMPORTANT: tick "Add Python to PATH" in the installer, then run this file again.
echo.
echo Python не найден. Установите Python 3.10+ с https://www.python.org/downloads/
echo ВАЖНО: в установщике поставьте галочку "Add Python to PATH", затем запустите файл снова.
pause
goto :eof

:error
echo.
echo Something went wrong. Check the message above.
pause
