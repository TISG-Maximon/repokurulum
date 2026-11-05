@echo off
REM ======================================================================
REM  kurulum.bat  -  Claude Code + Playwright MCP + graphify tam kurulum
REM  Calistirma: dosyaya cift tikla (yonetici GEREKMEZ, kendi kullanicinla calistir)
REM  Tekrar calistirmak guvenlidir (idempotent): kurulu olani atlar.
REM ======================================================================
setlocal EnableExtensions
chcp 65001 >nul
title Repo Kurulum - Claude Code / Playwright / graphify
cd /d "%~dp0"

set "ROOT=%~dp0"
set "LOGDIR=%ROOT%logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set "LOG=%LOGDIR%\kurulum.log"
set /a ERR=0
set /a WARN=0

>>"%LOG%" echo.
>>"%LOG%" echo ==================== %DATE% %TIME% ====================

call :log "Kurulum basladi. Log dosyasi: %LOG%"

REM ---------------------------------------------------------------- 0) On kontroller
ver | find "10." >nul || call :warn "Windows 10/11 disinda bir surum algilandi, sorun cikabilir."

net session >nul 2>&1
if %errorlevel%==0 call :warn "Yonetici olarak calisiyorsun. Normal kullanici olarak calistirman onerilir (araclar o kullaniciya kurulur)."

where winget >nul 2>&1
if errorlevel 1 (
  call :fail "winget bulunamadi. Microsoft Store'dan 'App Installer' (Uygulama Yukleyici) kurup tekrar calistir."
  goto :ozet
)

REM winget kaynak sozlesmelerini bir kere kabul et (ilk calismada takilmasin)
winget source update >>"%LOG%" 2>&1

REM ---------------------------------------------------------------- 1) Temel araclar
call :ensure git     Git.Git
call :ensure node    OpenJS.NodeJS.LTS
call :ensure uv      astral-sh.uv
call :ensure_chrome

REM Git ayarlari (uzun yol + satir sonu) - Windows'ta klasik hatalari onler
where git >nul 2>&1 && (
  git config --global core.longpaths true
  git config --global core.autocrlf true
)

REM ---------------------------------------------------------------- 2) Claude Code
call :install_claude

REM MCP sunucusu ilk acilista npx paket indirirken zaman asimina dusmesin
setx MCP_TIMEOUT 60000 >nul
set "MCP_TIMEOUT=60000"

REM ---------------------------------------------------------------- 3) Playwright MCP
call :install_playwright

REM ---------------------------------------------------------------- 4) graphify
call :install_graphify

REM ---------------------------------------------------------------- 5) Opsiyonel MCP'ler
echo.
choice /c EH /n /t 15 /d H /m "Ek MCP sunuculari (context7, sequential-thinking, GitHub) kurulsun mu? [E/H] (15 sn sonra H): "
if errorlevel 2 goto :ozet
call "%ROOT%scripts\mcp-ekstra.bat"
if errorlevel 1 set /a WARN+=1

goto :ozet


REM ======================================================================
REM  ALT PROGRAMLAR
REM ======================================================================

:log
echo [%TIME:~0,8%] %~1
>>"%LOG%" echo [%TIME:~0,8%] %~1
exit /b 0

:warn
set /a WARN+=1
call :log "[UYARI] %~1"
exit /b 0

:fail
set /a ERR+=1
call :log "[HATA]  %~1"
exit /b 1

:refresh_path
REM winget/npm/uv kurulumundan sonra yeni PATH'i bu pencereye yukle
for /f "usebackq tokens=* delims=" %%P in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "[Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')"`) do set "PATH=%%P"
set "PATH=%PATH%;%USERPROFILE%\.local\bin;%APPDATA%\npm;%ProgramFiles%\nodejs;%ProgramFiles%\Git\cmd"
exit /b 0

:ensure
REM %1 = kontrol edilecek komut, %2 = winget paket kimligi
where %1 >nul 2>&1
if %errorlevel%==0 (
  call :log "[OK]    %1 zaten kurulu"
  exit /b 0
)
call :log "[..]    %2 kuruluyor (winget)..."
winget install --id %2 -e --source winget --silent --accept-package-agreements --accept-source-agreements >>"%LOG%" 2>&1
call :refresh_path
where %1 >nul 2>&1
if %errorlevel%==0 (
  call :log "[OK]    %1 kuruldu"
  exit /b 0
)
call :fail "%2 kurulamadi. Log'a bak; elle: winget install --id %2 -e"
exit /b 1

:ensure_chrome
REM Playwright MCP varsayilan olarak sistemdeki Google Chrome'u kullanir
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" goto :chrome_ok
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" goto :chrome_ok
if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" goto :chrome_ok
call :log "[..]    Google Chrome kuruluyor (Playwright MCP icin)..."
winget install --id Google.Chrome -e --source winget --silent --accept-package-agreements --accept-source-agreements >>"%LOG%" 2>&1
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" goto :chrome_ok
if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" goto :chrome_ok
call :warn "Chrome kurulamadi. Playwright MCP icinde 'browser_install' aracini kullanabilir ya da Chrome'u elle kurabilirsin."
exit /b 0
:chrome_ok
call :log "[OK]    Google Chrome mevcut"
exit /b 0

:install_claude
where claude >nul 2>&1
if %errorlevel%==0 (
  call :log "[OK]    Claude Code zaten kurulu"
  goto :claude_update
)
call :log "[..]    Claude Code kuruluyor (resmi native installer)..."
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://claude.ai/install.ps1 | iex" >>"%LOG%" 2>&1
call :refresh_path
where claude >nul 2>&1
if %errorlevel%==0 goto :claude_ok
call :log "[..]    Native installer basarisiz, npm ile deneniyor..."
call npm install -g @anthropic-ai/claude-code >>"%LOG%" 2>&1
call :refresh_path
where claude >nul 2>&1
if %errorlevel%==0 goto :claude_ok
call :fail "Claude Code kurulamadi. Elle: npm install -g @anthropic-ai/claude-code"
exit /b 1
:claude_update
call claude update >>"%LOG%" 2>&1
:claude_ok
for /f "tokens=*" %%V in ('claude --version 2^>nul') do call :log "[OK]    Claude Code %%V"
exit /b 0

:install_playwright
where claude >nul 2>&1 || (call :fail "Claude yok, Playwright MCP eklenemedi." & exit /b 1)
where npx >nul 2>&1 || (call :fail "npx yok (Node.js kurulmamis), Playwright MCP eklenemedi." & exit /b 1)
call :log "[..]    Playwright MCP paketi onbellege indiriliyor (ilk acilis hizli olsun)..."
call npx -y @playwright/mcp@latest --help >>"%LOG%" 2>&1
REM Varsa eskisini sil, sonra kullanici (user) kapsaminda ekle -> tum projelerde gecerli
call claude mcp remove playwright -s user >nul 2>&1
call claude mcp add -s user playwright -- cmd /c npx -y @playwright/mcp@latest >>"%LOG%" 2>&1
if errorlevel 1 (
  call :fail "Playwright MCP eklenemedi. Elle: claude mcp add -s user playwright -- cmd /c npx -y @playwright/mcp@latest"
  exit /b 1
)
call :log "[OK]    Playwright MCP eklendi (scope: user)"
exit /b 0

:install_graphify
where uv >nul 2>&1 || (call :fail "uv yok, graphify kurulamadi." & exit /b 1)
call :log "[..]    graphify kuruluyor (uv, izole Python 3.12)..."
REM uv kendi Python'unu indirir -> sistemdeki Python / Store alias sorunlarindan etkilenmez
uv tool install --python 3.12 --force "graphifyy[mcp,pdf,office]" >>"%LOG%" 2>&1
if errorlevel 1 (
  call :warn "Ekstralarla kurulum basarisiz, sade paket deneniyor..."
  uv tool install --python 3.12 --force "graphifyy[mcp]" >>"%LOG%" 2>&1
)
uv tool update-shell >>"%LOG%" 2>&1
call :refresh_path
where graphify >nul 2>&1
if errorlevel 1 (
  call :fail "graphify komutu bulunamadi. Yeni bir terminal acip 'graphify --help' dene."
  exit /b 1
)
REM Skill'i Claude Code'a kaydet (~\.claude\skills\graphify\)
graphify install >>"%LOG%" 2>&1
if errorlevel 1 graphify install --platform windows >>"%LOG%" 2>&1
if errorlevel 1 (
  call :fail "graphify skill kaydi basarisiz. Elle: graphify install"
  exit /b 1
)
call :log "[OK]    graphify kuruldu ve /graphify skill'i Claude Code'a kaydedildi"
exit /b 0


:ozet
echo.
echo ======================================================================
call :log "BITTI.  Hata: %ERR%   Uyari: %WARN%"
echo ======================================================================
if %ERR% GTR 0 (
  echo  Bazi adimlar basarisiz. Ayrinti: "%LOG%"
  echo  Duzelttikten sonra bu dosyayi tekrar calistirabilirsin.
) else (
  echo  Sonraki adimlar:
  echo   1^) YENI bir terminal ac ^(PATH yenilensin^)
  echo   2^) Proje klasorunde:  claude          ^(ilk acilista tarayicidan giris yap^)
  echo   3^) Claude icinde:     /mcp            ^(playwright "connected" olmali^)
  echo   4^) Claude icinde:     /graphify .     ^(proje bilgi grafigini olustur^)
  echo   5^) Dogrulama:         scripts\dogrula.bat
)
echo.
pause
endlocal & exit /b %ERR%
