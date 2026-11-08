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
$S = "$E[0m"; $G = "$E[90m"; $C = "$E[36m"; $M = "$E[35m"; $K = "$E[1m"

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
    $k = $t - (Get-Date)
    if ($k.TotalMinutes -lt 0) { return 'simdi' }
    if ($k.TotalHours -ge 24) { return $t.ToString('ddd HH:mm', [Globalization.CultureInfo]::GetCultureInfo('tr-TR')) }
    return ('{0}sa{1:00}dk' -f [int][Math]::Floor($k.TotalHours), $k.Minutes)
}
function Limit([string]$Ad, $L) {
    if (-not $L -or $null -eq $L.used_percentage) { return "${G}${Ad}: -${S}" }
    $y = [double]$L.used_percentage
    return ('{0}: {1}{2:0}% [{3}]{4} {5}sifirlanma {6}{4}' -f $Ad, (Renk $y), $y, (Cubuk $y), $S, $G, (KalanSure $L.resets_at))
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
        $s = $satirlar[$i]
        if ($s.Length -gt 300000 -or $s -notmatch 'tool_use') { continue }
        try { $o = $s | ConvertFrom-Json } catch { continue }
        $icerik = @($o.message.content)
        for ($k = $icerik.Count - 1; $k -ge 0 -and -not $arac; $k--) {
            $c = $icerik[$k]
            if ($c.type -ne 'tool_use') { continue }
            $ad = [string]$c.name
            if ($ad -like 'mcp__*') {
                $p = $ad -split '__'
                $sunucu = $p[1] -replace '^plugin_[^_]+_', ''
                $arac = "$sunucu > $($p[2])"
            } elseif ($ad -eq 'Skill') { $arac = "skill > $($c.input.skill)" }
            elseif ($ad -in @('Agent', 'Task')) {
                $tip = $c.input.subagent_type; if (-not $tip) { $tip = 'genel' }
                $arac = "ajan > $tip"
            } else { $arac = $ad }
        }
    }
}

$s1 = "${K}${C}$model${S}"
if ($efor) { $s1 += " ${G}efor:${S}$efor" }
$s1 += "  ${G}|${S}  ${K}$proje${S}"
if ($dal) { $s1 += " ${G}($dal)${S}" }
if ($j.agent.name) { $s1 += "  ${G}|${S}  ${M}ajan: $($j.agent.name)${S}" }
if ($arac) { $s1 += "  ${G}|${S}  son arac: ${M}$arac${S}" }

# ---- 2. satir --------------------------------------------------------------
$cw = $j.context_window
if ($null -ne $cw.used_percentage) {
    $y = [double]$cw.used_percentage
    $boyut = [double]$cw.context_window_size
    if (-not $boyut) { $boyut = 200000 }
    $kul = $boyut * $y / 100
    $baglam = ('Baglam: {0}{1:0}% [{2}]{3} {4}/{5} {6}kalan {7}{3}' -f (Renk $y), $y, (Cubuk $y), $S, (Kisa $kul), (Kisa $boyut), $G, (Kisa ($boyut - $kul)))
} else { $baglam = "${G}Baglam: -${S}" }

$rl = $j.rate_limits
if ($rl) { $limitler = (Limit '5 saat' $rl.five_hour) + "  ${G}|${S}  " + (Limit 'Haftalik' $rl.seven_day) }
else { $limitler = "${G}Limit: ilk cevaptan sonra gorunur${S}" }

$tok = [double]$cw.total_input_tokens + [double]$cw.total_output_tokens
$oturum = ('{0}Oturum: {1} token' -f $G, (Kisa $tok))
if ($null -ne $j.cost.total_cost_usd) { $oturum += (' ~${0:0.00}' -f [double]$j.cost.total_cost_usd) }
$oturum += $S

Write-Output $s1
Write-Output ("$baglam  ${G}|${S}  $limitler  ${G}|${S}  $oturum")
