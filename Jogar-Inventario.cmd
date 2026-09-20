@echo off
title Platform2D - Parte 13 - Arsenal de Campo
cd /d "%~dp0"
echo A iniciar ARSENAL DE CAMPO. K ou X: disparar. H: usar kit. F3: comandos.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m examples.ranged --template inventory %*
) else (
  py -m examples.ranged --template inventory %*
)
if errorlevel 1 pause
