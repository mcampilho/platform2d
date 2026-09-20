@echo off
cd /d "%~dp0"
call Editor.cmd --profile campaign --output levels\minha-campanha.json %*
