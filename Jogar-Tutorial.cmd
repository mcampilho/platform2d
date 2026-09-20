@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" tutorials\first_game\main.py %*
) else (
  py tutorials\first_game\main.py %*
)
if errorlevel 1 pause
