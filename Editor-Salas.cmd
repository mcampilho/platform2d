@echo off
cd /d "%~dp0"
call Editor.cmd --profile rooms --output levels\meu-mundo.json %*
