@echo off
cd /d "%~dp0"
call Editor.cmd --profile adventure --output levels\minha-aventura.json %*
