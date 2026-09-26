@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m examples.environment %*
) else (
  py -3 -m examples.environment %*
)
if errorlevel 1 pause
