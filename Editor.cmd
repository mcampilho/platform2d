@echo off
title Platform2D - Parte 23 - Atelier - Campanhas
cd /d "%~dp0"
echo A iniciar ATELIER: editor visual. F5 testa o nivel; Ctrl+S guarda.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m examples.editor %*
) else (
  py -m examples.editor %*
)
if errorlevel 1 pause
