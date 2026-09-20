@echo off
cd /d "%~dp0"
call Editor.cmd --profile mechanisms --output levels\minha-central.json %*
