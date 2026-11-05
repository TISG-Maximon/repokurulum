@echo off
REM ======================================================================
REM  RepoKurulum.bat - Kurulum UYGULAMASINI (pencereli) baslatir.
REM  Cift tikla. Yonetici GEREKMEZ.
REM  Sessiz kurulum:  RepoKurulum.bat -Sessiz
REM  Durum listesi :  RepoKurulum.bat -Liste
REM ======================================================================
setlocal
cd /d "%~dp0"
powershell -NoProfile -Command "Get-ChildItem -LiteralPath '%~dp0' -Recurse -File | Unblock-File" >nul 2>&1
if "%~1"=="" (
  start "" powershell -NoProfile -ExecutionPolicy Bypass -STA -WindowStyle Hidden -File "%~dp0installer\RepoKurulum.ps1"
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0installer\RepoKurulum.ps1" %*
  pause
)
endlocal
