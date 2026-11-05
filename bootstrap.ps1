# ======================================================================
#  RepoKurulum bootstrap - herhangi bir Windows PC'de TEK SATIRLA baslatir:
#
#    irm https://raw.githubusercontent.com/TISG-Maximon/repokurulum/HEAD/bootstrap.ps1 | iex
#
#  Ne yapar: repoyu (git gerekmeden) ZIP olarak indirir,
#  %LOCALAPPDATA%\RepoKurulum\app klasorune acar ve kurulum uygulamasini baslatir.
#  Her calistirmada en guncel surumu indirir.
#
#  Istege bagli ortam degiskenleri (irm | iex param almadigi icin):
#    $env:REPOKURULUM_DAL        = 'HEAD'                      (dal/etiket/commit)
#    $env:REPOKURULUM_SESSIZ     = '1'                         (pencere acmadan varsayilanlari kur)
#    $env:REPOKURULUM_BILESENLER = 'claude,playwright-mcp'     (sessiz modda secim)
# ======================================================================
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
} catch { }

$Repo = 'TISG-Maximon/repokurulum'
$Dal = 'HEAD'
if ($env:REPOKURULUM_DAL) { $Dal = $env:REPOKURULUM_DAL }
$Kok = Join-Path $env:LOCALAPPDATA 'RepoKurulum'
$Hedef = Join-Path $Kok 'app'

try {
    Write-Host "RepoKurulum indiriliyor ($Repo @ $Dal)..." -ForegroundColor Cyan
    $tmp = Join-Path $env:TEMP ('repokurulum_' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    $zip = Join-Path $tmp 'repo.zip'

    $basarili = $false
    for ($deneme = 1; $deneme -le 4 -and -not $basarili; $deneme++) {
        try {
            Invoke-WebRequest -UseBasicParsing -Uri "https://codeload.github.com/$Repo/zip/$Dal" -OutFile $zip
            $basarili = $true
        } catch {
            if ($deneme -eq 4) { throw }
            $bekle = [Math]::Pow(2, $deneme)
            Write-Host "Indirme basarisiz, $bekle sn sonra tekrar ($deneme/4)..." -ForegroundColor Yellow
            Start-Sleep -Seconds $bekle
        }
    }

    Expand-Archive -LiteralPath $zip -DestinationPath $tmp -Force
    $kaynak = Get-ChildItem -LiteralPath $tmp -Directory | Select-Object -First 1
    if (-not $kaynak) { throw 'ZIP icinde klasor bulunamadi.' }

    New-Item -ItemType Directory -Force -Path $Kok | Out-Null
    if (Test-Path -LiteralPath $Hedef) {
        try { Remove-Item -LiteralPath $Hedef -Recurse -Force }
        catch { $Hedef = Join-Path $Kok ('app_' + (Get-Date -Format 'yyyyMMddHHmmss')) }   # eski surum aciksa
    }
    Move-Item -LiteralPath $kaynak.FullName -Destination $Hedef
    Get-ChildItem -LiteralPath $Hedef -Recurse -File | Unblock-File
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue

    $uygulama = Join-Path $Hedef 'installer\RepoKurulum.ps1'
    $arglar = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-STA', '-File', $uygulama)
    if ($env:REPOKURULUM_SESSIZ -eq '1') {
        $arglar += '-Sessiz'
        if ($env:REPOKURULUM_BILESENLER) { $arglar += @('-Bilesenler', $env:REPOKURULUM_BILESENLER) }
        & powershell.exe @arglar
        Write-Host "Bitti. Cikis kodu: $LASTEXITCODE" -ForegroundColor Cyan
    } else {
        Start-Process -FilePath 'powershell.exe' -ArgumentList $arglar -WindowStyle Hidden
        Write-Host "Kurulum penceresi aciliyor: $Hedef" -ForegroundColor Green
    }
} catch {
    Write-Host "HATA: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Elle: https://github.com/$Repo adresinden ZIP indirip RepoKurulum.bat'i calistir." -ForegroundColor Yellow
}
