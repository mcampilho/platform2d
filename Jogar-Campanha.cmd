@echo off
cd /d "%~dp0"
echo A iniciar CAMPANHA. Menu inicial: Nova campanha ou Continuar. F6: guardar. Esc: pausa.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m examples.campaign %*
) else (
  py -m examples.campaign %*
)
if errorlevel 1 pause
