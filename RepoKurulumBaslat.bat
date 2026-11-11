@echo off
REM ======================================================================
REM  RepoKurulumBaslat.bat - Repo Kurulum uygulamasini HER ZAMAN en son
REM  surumuyle indirip acar. Tek basina calisir; masaustune koyup cift tikla.
REM  Yonetici izni GEREKMEZ.
REM ======================================================================
setlocal
title Repo Kurulum
echo.
echo  Repo Kurulum indiriliyor ve aciliyor...
echo  (Kurulum penceresini kapatana kadar bu pencereyi KAPATMA)
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor 3072; irm https://raw.githubusercontent.com/TISG-Maximon/repokurulum/HEAD/bootstrap.ps1 | iex"
if errorlevel 1 (
  echo.
  echo  [HATA] Kurulum baslatilamadi. Internet baglantisini kontrol et.
  echo  Log klasoru: %LOCALAPPDATA%\RepoKurulum\logs
  pause
  exit /b 1
)
echo.
echo  Kurulum penceresi kapandi.
timeout /t 5 >nul
endlocal
