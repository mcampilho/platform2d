@echo off
cd /d "%~dp0"
call Editor.cmd --profile cargo --output levels\meu-cargo.json %*
