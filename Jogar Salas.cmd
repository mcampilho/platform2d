@echo off
title Platform2D - Parte 2 - Arquivo Lunar
cd /d "%~dp0"
echo A iniciar PARTE 2: ARQUIVO LUNAR - duas salas e plataformas moveis.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m examples.rooms %*
) else (
  py -m examples.rooms %*
)
if errorlevel 1 pause
