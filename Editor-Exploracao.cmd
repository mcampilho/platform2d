@echo off
cd /d "%~dp0"
call Editor.cmd --profile explore --output levels\meu-explore.json %*
