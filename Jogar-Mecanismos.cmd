@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m examples.mechanisms %*
) else (
  py -m examples.mechanisms %*
)
if errorlevel 1 pause
