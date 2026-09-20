@echo off
title Platform2D - Parte 12 - Linha de Defesa
cd /d "%~dp0"
echo A iniciar LINHA DE DEFESA. K ou X: disparar. F3: comandos.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m examples.ranged %*
) else (
  py -m examples.ranged %*
)
if errorlevel 1 pause
