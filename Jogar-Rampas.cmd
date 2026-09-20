@echo off
title Platform2D - Parte 11 - Colinas
cd /d "%~dp0"
echo A iniciar COLINAS: rampas, cristais e salto sobre o fosso.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m examples.slopes %*
) else (
  py -m examples.slopes %*
)
if errorlevel 1 pause
