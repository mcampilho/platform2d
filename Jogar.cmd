@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m examples.classic
) else (
  py -m examples.classic
)
if errorlevel 1 pause
