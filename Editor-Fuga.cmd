@echo off
cd /d "%~dp0"
call Editor.cmd --profile escape --output levels\meu-escape.json %*
