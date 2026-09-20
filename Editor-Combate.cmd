@echo off
cd /d "%~dp0"
call Editor.cmd --profile ranged --output levels\meu-combate.json %*
