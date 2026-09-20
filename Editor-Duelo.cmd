@echo off
cd /d "%~dp0"
call Editor.cmd --profile duel --output levels\meu-duelo.json %*
