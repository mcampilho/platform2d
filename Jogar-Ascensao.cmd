@echo off
title Platform2D - Parte 4 - Ascensao
cd /d "%~dp0"
echo A iniciar PARTE 4: ASCENSAO - dash, saltos na parede e escadas.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m examples.precision %*
) else (
  py -m examples.precision %*
)
if errorlevel 1 pause
