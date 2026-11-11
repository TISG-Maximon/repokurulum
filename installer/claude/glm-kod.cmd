@echo off
REM repokurulum: GLM ile calisan Claude Code (ayni arac, farkli model saglayicisi).
REM Ana Claude oturumunu ve aboneligini ETKILEMEZ: ayarlar sadece bu islem icin gecerlidir.
REM Kullanim:  glm-kod -p "gorev" --permission-mode acceptEdits
REM Model degistirmek icin:  setx GLM_MODEL glm-5.3-flash   (varsayilan: glm-5.3)
setlocal EnableExtensions
if "%ZAI_API_KEY%"=="" for /f "usebackq tokens=*" %%K in (`powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('ZAI_API_KEY','User')"`) do set "ZAI_API_KEY=%%K"
if "%ZAI_API_KEY%"=="" (
  echo [HATA] ZAI_API_KEY tanimli degil. RepoKurulum ile "GLM kod ajanlari" bilesenini kur.
  exit /b 1
)
if "%GLM_MODEL%"=="" for /f "usebackq tokens=*" %%M in (`powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('GLM_MODEL','User')"`) do set "GLM_MODEL=%%M"
if "%GLM_MODEL%"=="" set "GLM_MODEL=glm-5.3"
set "ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic"
set "ANTHROPIC_AUTH_TOKEN=%ZAI_API_KEY%"
set "ANTHROPIC_API_KEY="
set "ANTHROPIC_MODEL=%GLM_MODEL%"
set "ANTHROPIC_DEFAULT_OPUS_MODEL=%GLM_MODEL%"
set "ANTHROPIC_DEFAULT_SONNET_MODEL=%GLM_MODEL%"
set "ANTHROPIC_DEFAULT_HAIKU_MODEL=%GLM_MODEL%"
set "CLAUDE_CODE_SUBAGENT_MODEL=%GLM_MODEL%"
set "API_TIMEOUT_MS=3000000"
set "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1"
REM Hafiza ve limit hook'lari GLM oturumlarinda calismasin
set "REPOKURULUM_GLM=1"
call claude %*
exit /b %ERRORLEVEL%
