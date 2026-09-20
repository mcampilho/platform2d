@echo off
cd /d "%~dp0"
call Editor.cmd --profile swim --output levels\meu-swim.json %*
