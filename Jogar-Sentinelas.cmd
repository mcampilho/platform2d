@echo off
title Platform2D - Parte 3 - Sentinelas
cd /d "%~dp0"
echo A iniciar PARTE 3: SENTINELAS - guardas, combate e interacao.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m examples.sentinels %*
) else (
  py -m examples.sentinels %*
)
if errorlevel 1 pause
