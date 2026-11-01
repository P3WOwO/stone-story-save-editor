@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
)
".venv\Scripts\python.exe" -m pip install -q -r requirements.txt pyinstaller
if errorlevel 1 goto :error
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed ^
    --name StoneStorySaveEditor --hidden-import=pprp.crypto_3 main.py
if errorlevel 1 goto :error
echo.
echo Done: dist\StoneStorySaveEditor.exe
pause
goto :eof
:error
echo Build failed.
pause
