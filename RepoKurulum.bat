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
echo Kurulum penceresi aciliyor... Bu siyah pencereyi KAPATMA.
powershell -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0installer\RepoKurulum.ps1" %*
if errorlevel 1 (
  echo.
  echo Uygulama hata ile kapandi. Log: %LOCALAPPDATA%\RepoKurulum\logs
  pause
) else (
  if not "%~1"=="" pause
)
endlocal
