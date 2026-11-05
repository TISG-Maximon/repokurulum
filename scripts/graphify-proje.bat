@echo off
REM ======================================================================
REM  graphify-proje.bat - Bir PROJE klasorunde graphify'i etkinlestirir
REM  Kullanim:  scripts\graphify-proje.bat "C:\yol\projem"
REM            (parametre verilmezse bulunulan klasor kullanilir)
REM  Yaptiklari:
REM   1) graphify claude install  -> CLAUDE.md kurali + PreToolUse hook
REM      (Claude, Grep/Glob yapmadan once grafigi sorgular)
REM   2) graph.json varsa graphify MCP sunucusunu proje kapsaminda ekler
REM ======================================================================
setlocal EnableExtensions
set "PROJE=%~1"
if "%PROJE%"=="" set "PROJE=%CD%"
if not exist "%PROJE%\" (echo [HATA] Klasor yok: "%PROJE%" & exit /b 1)
cd /d "%PROJE%"

where graphify >nul 2>&1 || (echo [HATA] graphify yok. Once kurulum.bat calistir. & exit /b 1)
where claude   >nul 2>&1 || (echo [HATA] claude yok. Once kurulum.bat calistir. & exit /b 1)

echo [..] graphify Claude entegrasyonu: "%CD%"
graphify claude install
if errorlevel 1 (echo [HATA] graphify claude install basarisiz. & exit /b 1)

if not exist "%CD%\graphify-out\graph.json" (
  echo.
  echo [BILGI] Henuz grafik yok. Simdi su adimlari yap:
  echo    1^) Bu klasorde:  claude
  echo    2^) Claude icinde: /graphify .
  echo    3^) Bittikten sonra bu dosyayi tekrar calistir ^(MCP baglanir^).
  exit /b 0
)

call claude mcp remove graphify -s project >nul 2>&1
where graphify-mcp >nul 2>&1
if %errorlevel%==0 (
  call claude mcp add -s project graphify -- graphify-mcp "%CD%\graphify-out\graph.json"
) else (
  call claude mcp add -s project graphify -- uvx --python 3.12 --from "graphifyy[mcp]" python -m graphify.serve "%CD%\graphify-out\graph.json"
)
if errorlevel 1 (echo [HATA] graphify MCP eklenemedi. & exit /b 1)
echo [OK] graphify MCP eklendi (.mcp.json). Claude'u yeniden baslat ve /mcp ile kontrol et.
endlocal & exit /b 0
