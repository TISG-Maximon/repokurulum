@echo off
REM ======================================================================
REM  dogrula.bat - Kurulumu kontrol eder, hicbir sey degistirmez
REM ======================================================================
setlocal EnableExtensions
set /a EKSIK=0
echo ---- Araclar ----
call :chk git     "git --version"
call :chk node    "node --version"
call :chk npx     "npx --version"
call :chk uv      "uv --version"
call :chk claude  "claude --version"
call :chk graphify "graphify --help"
echo.
echo ---- graphify skill ----
if exist "%USERPROFILE%\.claude\skills\graphify\SKILL.md" (echo [OK] %USERPROFILE%\.claude\skills\graphify\SKILL.md) else (echo [EKSIK] graphify skill kaydi yok -^> graphify install & set /a EKSIK+=1)
echo.
echo ---- MCP sunuculari (claude mcp list) ----
where claude >nul 2>&1 && call claude mcp list
echo.
echo ---- MCP_TIMEOUT ----
if "%MCP_TIMEOUT%"=="" (echo [UYARI] MCP_TIMEOUT tanimli degil ^(yeni terminal actin mi?^)) else (echo [OK] MCP_TIMEOUT=%MCP_TIMEOUT%)
echo.
if %EKSIK%==0 (echo SONUC: Her sey hazir.) else (echo SONUC: %EKSIK% eksik var. kurulum.bat'i tekrar calistir.)
pause
endlocal & exit /b %EKSIK%

:chk
where %1 >nul 2>&1
if errorlevel 1 (
  echo [EKSIK] %1
  set /a EKSIK+=1
  exit /b 0
)
for /f "tokens=1,* delims=:" %%A in ('%~2 2^>nul ^| findstr /n "^" ^| findstr "^1:"') do echo [OK] %1  %%B
exit /b 0
