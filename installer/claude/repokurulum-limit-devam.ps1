# repokurulum: Kullanim limiti dolunca sifirlanmayi bekler, sonra Claude'u kaldigi yerden onay beklemeden devam ettirir.
#
# Claude Code "StopFailure" hook'u (matcher: rate_limit) olarak, "asyncRewake": true ile calisir:
#   - Tur limit nedeniyle bittiginde tetiklenir, arka planda bekler (Claude'u kilitlemez).
#   - Sifirlanma zamani: 1) durum satirinin kaydettigi limit-durum.json (resets_at)
#                        2) hata metnindeki "resets 1:40pm (UTC)" ifadesi
#                        3) ikisi de yoksa 30 dakika
#   - Sure dolunca cikis kodu 2 ve stderr mesaji ile modeli uyandirir -> Claude kaldigi yerden devam eder.
#   - Haftalik limit gibi uzun beklemelerde en fazla ~6 saat bekler; limit hala doluysa hook yeniden tetiklenir ve beklemeye devam eder.
# Log: %LOCALAPPDATA%\RepoKurulum\logs\limit-devam.log
$ErrorActionPreference = 'SilentlyContinue'
$Utf8 = New-Object System.Text.UTF8Encoding($false)
$Kok = Join-Path $env:LOCALAPPDATA 'RepoKurulum'
$LogYolu = Join-Path $Kok 'logs\limit-devam.log'
New-Item -ItemType Directory -Force -Path (Split-Path $LogYolu) | Out-Null
$AzamiBeklemeSn = 21300   # hook zaman asimi (21600) dolmadan uyan

function Log([string]$m) {
    try { [IO.File]::AppendAllText($LogYolu, ('[{0:yyyy-MM-dd HH:mm:ss}] {1}' -f (Get-Date), $m) + "`r`n", $Utf8) } catch { }
}

try { $girdi = [Console]::In.ReadToEnd() | ConvertFrom-Json } catch { exit 0 }
if ($girdi.error -and $girdi.error -ne 'rate_limit') { exit 0 }
$oturum = [string]$girdi.session_id
if (-not $oturum) { $oturum = 'bilinmiyor' }

# Ayni oturum icin tek bekleyici
$kilit = Join-Path $Kok ('limit-bekleyen-' + ($oturum -replace '[^A-Za-z0-9\-]', '') + '.txt')
# Kilit 30 sn'de bir tazelenir; 2 dakikadan eskiyse onceki bekleyici olmus demektir
if ((Test-Path -LiteralPath $kilit) -and ((Get-Item -LiteralPath $kilit).LastWriteTime -gt (Get-Date).AddSeconds(-120))) {
    Log "Bu oturum icin zaten bekleyen var ($oturum), cikiliyor"
    exit 0
}
[IO.File]::WriteAllText($kilit, (Get-Date).ToString('o'), $Utf8)

try {
    $simdi = Get-Date
    $hedef = $null
    $kaynak = ''

    # 1) Durum satirinin kaydettigi limit bilgisi (dolu olan pencerenin sifirlanma zamani)
    $limitDosyasi = Join-Path $Kok 'limit-durum.json'
    if (Test-Path -LiteralPath $limitDosyasi) {
        try {
            $l = [IO.File]::ReadAllText($limitDosyasi) | ConvertFrom-Json
            foreach ($ad in @('five_hour', 'seven_day')) {
                $w = $l.$ad
                if (-not $w -or -not $w.resets_at) { continue }
                $t = [DateTimeOffset]::FromUnixTimeSeconds([long]$w.resets_at).LocalDateTime
                if ($t -le $simdi) { continue }
                if ([double]$w.used_percentage -ge 95) {
                    if (-not $hedef -or $t -gt $hedef) { $hedef = $t; $kaynak = "durum satiri ($ad, %$($w.used_percentage))" }
                }
            }
        } catch { }
    }

    # 2) Hata metni: "resets 1:40pm (UTC)", "resets at 13:40", "resets 9am"
    if (-not $hedef) {
        $metin = ([string]$girdi.error_details) + ' ' + ([string]$girdi.last_assistant_message)
        $m = [regex]::Match($metin, '(?i)resets?\s+(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*(?:\(([^)]+)\))?')
        if ($m.Success) {
            $saat = [int]$m.Groups[1].Value
            $dk = 0; if ($m.Groups[2].Success) { $dk = [int]$m.Groups[2].Value }
            $ampm = $m.Groups[3].Value.ToLower()
            if ($ampm -eq 'pm' -and $saat -lt 12) { $saat += 12 }
            if ($ampm -eq 'am' -and $saat -eq 12) { $saat = 0 }
            $tz = $m.Groups[4].Value
            if ($tz -match '(?i)UTC|GMT') {
                $u = [DateTime]::UtcNow
                $t = (New-Object DateTime($u.Year, $u.Month, $u.Day, $saat, $dk, 0, [DateTimeKind]::Utc)).ToLocalTime()
            } else {
                $t = $simdi.Date.AddHours($saat).AddMinutes($dk)
            }
            if ($t -le $simdi) { $t = $t.AddDays(1) }
            $hedef = $t; $kaynak = "hata metni ($($m.Value.Trim()))"
        }
    }

    # 3) Bilinmiyorsa 30 dakika sonra dene
    if (-not $hedef) { $hedef = $simdi.AddMinutes(30); $kaynak = 'bilinmiyor, 30 dk sonra denenecek' }

    $hedef = $hedef.AddSeconds(90)   # sifirlanmadan hemen sonra degil, biraz pay birak
    $azami = $simdi.AddSeconds($AzamiBeklemeSn)
    if ($hedef -gt $azami) { $hedef = $azami; $kaynak += '; uzun bekleme, ~6 saatte bir kontrol' }

    Log ("Limit doldu (oturum {0}). Uyanma: {1:yyyy-MM-dd HH:mm} - kaynak: {2}" -f $oturum, $hedef, $kaynak)
    if ($env:REPOKURULUM_LIMIT_TEST -eq '1') {
        # Test modu: beklemeden hesaplanan zamani yaz
        Write-Output ('HEDEF={0:o}' -f $hedef)
        Write-Output ('KAYNAK={0}' -f $kaynak)
        $hedef = Get-Date
    }
    while ((Get-Date) -lt $hedef) {
        Start-Sleep -Seconds 30
        [IO.File]::WriteAllText($kilit, (Get-Date).ToString('o'), $Utf8)   # bekleyicinin canli oldugunu goster
    }
    Log "Sure doldu, Claude uyandiriliyor (oturum $oturum)"
} finally {
    Remove-Item -LiteralPath $kilit -Force -ErrorAction SilentlyContinue
}

# Cikis kodu 2 + stderr: asyncRewake modeli bu mesajla uyandirir
[Console]::Error.WriteLine(("Kullanim limiti sifirlandi ({0:HH:mm}). Limit yuzunden yarim kalan isine KALDIGIN YERDEN devam et; kullaniciya onay sorma. " +
    "Once tek cumleyle son tamamlanan adimi ve simdi yapacagini yaz, sonra devam et. " +
    "Is zaten bittiyse ya da kullanici bu arada baska bir sey istediyse sadece bunu kisaca belirt.") -f (Get-Date))
exit 2
