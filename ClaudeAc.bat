@echo off
REM ======================================================================
REM  ClaudeAc.bat - Claude Code'u istedigin klasorde acar.
REM
REM  Kullanim:
REM    - Cift tikla: klasor ve konusma secimi sorulur
REM    - Bir klasoru bu dosyanin UZERINE SURUKLE-BIRAK: o klasorde acar
REM    - Komut satiri: ClaudeAc.bat "C:\projem" [yeni|devam|sec]
REM
REM  Masaustune kopyalayabilirsin; her yerden calisir.
REM  Son kullanilan klasor hatirlanir (%LOCALAPPDATA%\RepoKurulum\son-klasor.txt).
REM ======================================================================
setlocal EnableExtensions
title Claude Code
set "AYAR=%LOCALAPPDATA%\RepoKurulum"
set "SON=%AYAR%\son-klasor.txt"
if not exist "%AYAR%" mkdir "%AYAR%" >nul 2>&1

REM Claude'un kuruldugu yerler PATH'te olmayabilir (yeni kurulumdan sonra)
set "PATH=%PATH%;%USERPROFILE%\.local\bin;%APPDATA%\npm"
where claude >nul 2>&1
if errorlevel 1 (
  echo [HATA] Claude Code bulunamadi.
  echo        Once kurulumu calistir: RepoKurulum.bat
  goto :bitir_hata
)

set "KLASOR=%~1"
set "MOD=%~2"
if defined KLASOR goto :klasor_kontrol

REM ---------------------------------------------------------------- Klasor secimi
set "ONCEKI="
if exist "%SON%" set /p ONCEKI=<"%SON%"
echo.
echo  Claude Code hangi klasorde acilsin?
echo.
if defined ONCEKI echo    [1] Son klasor: %ONCEKI%
echo    [2] Klasor sec (pencere acilir)
echo    [3] Kullanici klasorum: %USERPROFILE%
echo.
choice /c 123 /n /m " Secim [1/2/3]: "
if errorlevel 3 (set "KLASOR=%USERPROFILE%" & goto :klasor_kontrol)
if errorlevel 2 goto :klasor_sec
if defined ONCEKI (set "KLASOR=%ONCEKI%" & goto :klasor_kontrol)

:klasor_sec
for /f "usebackq delims=" %%K in (`powershell -NoProfile -STA -Command "Add-Type -AssemblyName System.Windows.Forms; $f = New-Object System.Windows.Forms.Form; $f.TopMost = $true; $d = New-Object System.Windows.Forms.FolderBrowserDialog; $d.Description = 'Claude Code hangi klasorde calissin?'; $d.ShowNewFolderButton = $true; if ($d.ShowDialog($f) -eq 'OK') { $d.SelectedPath }"`) do set "KLASOR=%%K"
if not defined KLASOR (
  echo Klasor secilmedi.
  goto :bitir_hata
)

:klasor_kontrol
if not exist "%KLASOR%\" (
  echo [HATA] Klasor bulunamadi: "%KLASOR%"
  goto :bitir_hata
)
>"%SON%" echo %KLASOR%

REM ---------------------------------------------------------------- Konusma secimi
if /i "%MOD%"=="yeni"  goto :calistir
if /i "%MOD%"=="devam" goto :calistir
if /i "%MOD%"=="sec"   goto :calistir
echo.
echo    [1] Yeni konusma
echo    [2] Bu klasordeki son konusmaya devam et
echo    [3] Eski konusmalardan sec
echo.
choice /c 123 /n /m " Secim [1/2/3]: "
set "MOD=yeni"
if errorlevel 2 set "MOD=devam"
if errorlevel 3 set "MOD=sec"

:calistir
set "BAYRAK="
if /i "%MOD%"=="devam" set "BAYRAK=--continue"
if /i "%MOD%"=="sec"   set "BAYRAK=--resume"
cd /d "%KLASOR%"
title Claude Code - %KLASOR%
echo.
echo  Klasor : %KLASOR%
echo  Komut  : claude %BAYRAK%
echo  (Cikmak icin Claude icinde /exit yaz veya Ctrl+C'ye iki kez bas)
echo  Ilk kez acilan klasorde "Quick safety check" sorusu gelir: kendi klasorunse "Yes, I trust this folder" sec.
echo  Claude'a ilk girisinde tarayici acilir, hesabinla giris yap. Sonra /mcp ile sunuculari kontrol edebilirsin.
echo.
if "%CLAUDEAC_KURU%"=="1" (
  echo KURU CALISMA: claude %BAYRAK%
  endlocal & exit /b 0
)
REM Acmadan once Claude Code'u guncelle (yeni surum varsa indirilir; yoksa birkac saniye surer)
REM Atlamak icin: set CLAUDEAC_GUNCELLEME=0
if not "%CLAUDEAC_GUNCELLEME%"=="0" (
  echo  Claude Code guncelleme kontrolu...
  call claude update > "%AYAR%\claude-update.txt" 2>&1
  findstr /i /c:"updated" /c:"guncellendi" /c:"Successfully" "%AYAR%\claude-update.txt" >nul && echo  Claude Code guncellendi.
  findstr /i /c:"up to date" /c:"latest version" /c:"already" "%AYAR%\claude-update.txt" >nul && echo  Claude Code guncel.
  findstr /i /c:"Error" /c:"Failed" "%AYAR%\claude-update.txt" >nul && echo  Guncelleme yapilamadi; Claude mevcut surumle aciliyor. Ayrinti: %AYAR%\claude-update.txt
  echo.
)
call claude %BAYRAK%
echo.
echo  Claude kapandi.
pause
endlocal & exit /b 0

:bitir_hata
echo.
if not "%CLAUDEAC_KURU%"=="1" pause
endlocal & exit /b 1
