# repokurulum durum satiri (Claude Code statusLine)
# Yerelde calisir, API/token harcamaz. Claude Code her cevaptan sonra ve 30 sn'de bir
# oturum bilgisini JSON olarak stdin'e verir; bu betik 2 satir ozet yazar.
#   1. satir: model | varsayilan efor | proje (repo) + dal | son kullanilan arac (MCP/skill/ajan)
#   2. satir: baglam doluluk | 5 saatlik limit | haftalik limit | oturum token ve tahmini maliyet
$ErrorActionPreference = 'SilentlyContinue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

$ham = [Console]::In.ReadToEnd()
try { $j = $ham | ConvertFrom-Json } catch { Write-Output 'Claude'; exit 0 }

$E = [char]27
$RenkSifir = "$E[0m"; $RenkGri = "$E[90m"; $RenkCamgobegi = "$E[36m"; $RenkMor = "$E[35m"; $RenkKalin = "$E[1m"

function Renk([double]$y) {
    if ($y -ge 85) { return "$E[31m" }
    if ($y -ge 60) { return "$E[33m" }
    return "$E[32m"
}
function Cubuk([double]$y) {
    $n = [int][Math]::Round($y / 10)
    if ($n -lt 0) { $n = 0 }; if ($n -gt 10) { $n = 10 }
    return ('#' * $n) + ('-' * (10 - $n))
}
function Kisa([double]$t) {
    if ($t -ge 1000000) { return ('{0:0.0}M' -f ($t / 1000000)) }
    if ($t -ge 1000) { return ('{0:0}k' -f ($t / 1000)) }
    return ('{0:0}' -f $t)
}
function KalanSure($epoch) {
    if (-not $epoch) { return '' }
    $t = [DateTimeOffset]::FromUnixTimeSeconds([long]$epoch).LocalDateTime
    $fark = $t - (Get-Date)
    if ($fark.TotalMinutes -lt 0) { return 'simdi' }
    if ($fark.TotalHours -ge 24) { return $t.ToString('ddd HH:mm', [Globalization.CultureInfo]::GetCultureInfo('tr-TR')) }
    return ('{0}sa{1:00}dk' -f [int][Math]::Floor($fark.TotalHours), $fark.Minutes)
}
function Limit([string]$Ad, $L) {
    if (-not $L -or $null -eq $L.used_percentage) { return "${RenkGri}${Ad}: -${RenkSifir}" }
    $y = [double]$L.used_percentage
    return ('{0}: {1}{2:0}% [{3}]{4} {5}sifirlanma {6}{4}' -f $Ad, (Renk $y), $y, (Cubuk $y), $RenkSifir, $RenkGri, (KalanSure $L.resets_at))
}

# ---- 1. satir --------------------------------------------------------------
$model = $j.model.display_name
if (-not $model) { $model = $j.model.id }

$efor = ''
$ayarYolu = Join-Path $env:USERPROFILE '.claude\settings.json'
if ($env:CLAUDE_CODE_EFFORT_LEVEL) { $efor = $env:CLAUDE_CODE_EFFORT_LEVEL }
elseif (Test-Path -LiteralPath $ayarYolu) {
    try { $efor = ([IO.File]::ReadAllText($ayarYolu) | ConvertFrom-Json).effortLevel } catch { }
}

$dizin = $j.workspace.current_dir
if (-not $dizin) { $dizin = $j.cwd }
if ($j.workspace.repo.name) { $proje = "$($j.workspace.repo.owner)/$($j.workspace.repo.name)" }
else { $proje = Split-Path -Leaf $dizin }
$dal = ''
if ($dizin) { $dal = (& git -C "$dizin" branch --show-current 2>$null) }

# Son kullanilan arac: transkriptin son satirlarindaki en son tool_use
$arac = ''
if ($j.transcript_path -and (Test-Path -LiteralPath $j.transcript_path)) {
    $satirlar = @(Get-Content -LiteralPath $j.transcript_path -Tail 30 -Encoding UTF8)
    for ($i = $satirlar.Count - 1; $i -ge 0 -and -not $arac; $i--) {
        $tSatir = $satirlar[$i]
        if ($tSatir.Length -gt 300000 -or $tSatir -notmatch 'tool_use') { continue }
        try { $tKayit = $tSatir | ConvertFrom-Json } catch { continue }
        if ($tKayit.type -ne 'assistant') { continue }
        $icerik = @($tKayit.message.content)
        for ($ki = $icerik.Count - 1; $ki -ge 0 -and -not $arac; $ki--) {
            $parca = $icerik[$ki]
            if ($parca.type -ne 'tool_use') { continue }
            $ad = [string]$parca.name
            if ($ad -like 'mcp__*') {
                $adParca = $ad -split '__'
                $sunucu = $adParca[1] -replace '^plugin_[^_]+_', ''
                $arac = "$sunucu > $($adParca[2])"
            } elseif ($ad -eq 'Skill') { $arac = "skill > $($parca.input.skill)" }
            elseif ($ad -in @('Agent', 'Task')) {
                $tip = $parca.input.subagent_type; if (-not $tip) { $tip = 'genel' }
                $arac = "ajan > $tip"
            } else { $arac = $ad }
        }
    }
}

$s1 = "${RenkKalin}${RenkCamgobegi}$model${RenkSifir}"
if ($efor) { $s1 += " ${RenkGri}efor:${RenkSifir}$efor" }
$s1 += "  ${RenkGri}|${RenkSifir}  ${RenkKalin}$proje${RenkSifir}"
if ($dal) { $s1 += " ${RenkGri}($dal)${RenkSifir}" }
if ($j.agent.name) { $s1 += "  ${RenkGri}|${RenkSifir}  ${RenkMor}ajan: $($j.agent.name)${RenkSifir}" }
if ($arac) { $s1 += "  ${RenkGri}|${RenkSifir}  son arac: ${RenkMor}$arac${RenkSifir}" }

# ---- 2. satir --------------------------------------------------------------
$cw = $j.context_window
if ($null -ne $cw.used_percentage) {
    $y = [double]$cw.used_percentage
    $boyut = [double]$cw.context_window_size
    if (-not $boyut) { $boyut = 200000 }
    $kul = $boyut * $y / 100
    $baglam = ('Baglam: {0}{1:0}% [{2}]{3} {4}/{5} {6}kalan {7}{3}' -f (Renk $y), $y, (Cubuk $y), $RenkSifir, (Kisa $kul), (Kisa $boyut), $RenkGri, (Kisa ($boyut - $kul)))
} else { $baglam = "${RenkGri}Baglam: -${RenkSifir}" }

$rl = $j.rate_limits
if ($rl) { $limitler = (Limit '5 saat' $rl.five_hour) + "  ${RenkGri}|${RenkSifir}  " + (Limit 'Haftalik' $rl.seven_day) }
else { $limitler = "${RenkGri}Limit: ilk cevaptan sonra gorunur${RenkSifir}" }

$tok = [double]$cw.total_input_tokens + [double]$cw.total_output_tokens
$oturum = ('{0}Oturum: {1} token' -f $RenkGri, (Kisa $tok))
if ($null -ne $j.cost.total_cost_usd) { $oturum += (' ~${0:0.00}' -f [double]$j.cost.total_cost_usd) }
$oturum += $RenkSifir

Write-Output $s1
Write-Output ("$baglam  ${RenkGri}|${RenkSifir}  $limitler  ${RenkGri}|${RenkSifir}  $oturum")
