@echo off
cd /d "%~dp0"
if exist "artifacts\resgate-i18n-windows\ResgateNaEstacao\ResgateNaEstacao.exe" (
  start "" "artifacts\resgate-i18n-windows\ResgateNaEstacao\ResgateNaEstacao.exe" %*
) else (
  start "" "artifacts\windows-1.0.0\ResgateNaEstacao\ResgateNaEstacao.exe" %*
)
