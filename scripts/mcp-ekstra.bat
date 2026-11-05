@echo off
REM ======================================================================
REM  mcp-ekstra.bat - Opsiyonel MCP sunuculari (kullanici kapsami)
REM   - context7            : guncel kutuphane dokumantasyonu (anahtar gerekmez)
REM   - sequential-thinking : adim adim dusunme araci (anahtar gerekmez)
REM   - github              : GitHub resmi MCP (GITHUB_PAT ortam degiskeni gerekir)
REM ======================================================================
setlocal EnableExtensions
set /a FAILS=0

where claude >nul 2>&1 || (echo [HATA] claude bulunamadi, once kurulum.bat calistir. & exit /b 1)

call :add_npx context7 @upstash/context7-mcp@latest
call :add_npx sequential-thinking @modelcontextprotocol/server-sequential-thinking

if "%GITHUB_PAT%"=="" (
  echo [ATLANDI] GitHub MCP: GITHUB_PAT tanimli degil.
  echo           Token olustur: https://github.com/settings/personal-access-tokens
  echo           Sonra:  setx GITHUB_PAT "ghp_xxx"   ve bu dosyayi YENI terminalde tekrar calistir.
) else (
  call claude mcp remove github -s user >nul 2>&1
  call claude mcp add -s user --transport http github https://api.githubcopilot.com/mcp/ -H "Authorization: Bearer %GITHUB_PAT%"
  if errorlevel 1 (set /a FAILS+=1 & echo [HATA] GitHub MCP eklenemedi.) else (echo [OK] github MCP eklendi)
)

echo.
call claude mcp list
endlocal & exit /b %FAILS%

:add_npx
REM %1 = ad, %2 = npm paketi
call npx -y %2 --help >nul 2>&1
call claude mcp remove %1 -s user >nul 2>&1
call claude mcp add -s user %1 -- cmd /c npx -y %2
if errorlevel 1 (
  set /a FAILS+=1
  echo [HATA] %1 eklenemedi.
) else (
  echo [OK] %1 MCP eklendi
)
exit /b 0
