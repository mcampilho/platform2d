@echo off
cd /d "%~dp0"
call Jogar-Campanha.cmd --campaign "examples\campaign\assets\odyssey-duel.json" %*
