# repokurulum: Claude Code oturum ozetini NotebookLM "Claude Hafiza" notebook'una ekler.
#
# Claude Code hook'u olarak calisir (SessionEnd ve PreCompact). Hook cagrisi hemen doner;
# asil is arka planda yapilir (Claude'u bekletmez).
#   - Her ay icin tek bir kaynak: "Claude Hafiza YYYY-MM". Oturum ozetleri bu kaynagin sonuna eklenir
#     (NotebookLM kaynak sinirina takilmamak icin).
#   - Ayni oturumun ayni kismi iki kez gonderilmez (islenen satir sayisi tutulur).
#   - API anahtari, token, sifre gibi sirlar gonderilmeden once maskelenir.
#   - Gonderilemezse ozet %LOCALAPPDATA%\RepoKurulum\hafiza-bekleyen icine yazilir, sonraki sefer tekrar denenir.
# Elle kullanim:
#   powershell -File repokurulum-hafiza.ps1 -Hazirla     (notebook'u olusturur / bulur, kimligini yazar)
param(
    [switch]$Hazirla,
    [switch]$Arkaplan,
    [string]$Transkript = '',
    [string]$Oturum = '',
    [string]$Dizin = '',
    [string]$Olay = ''
)
$ErrorActionPreference = 'Stop'
$NotebookAdi = 'Claude Hafiza'
$DurumYolu = Join-Path $env:USERPROFILE '.claude\repokurulum-hafiza.json'
$Bekleyen = Join-Path $env:LOCALAPPDATA 'RepoKurulum\hafiza-bekleyen'
$LogYolu = Join-Path $env:LOCALAPPDATA 'RepoKurulum\logs\hafiza.log'
New-Item -ItemType Directory -Force -Path (Split-Path $LogYolu), $Bekleyen, (Split-Path $DurumYolu) | Out-Null
$Utf8 = New-Object System.Text.UTF8Encoding($false)

function Log([string]$m) {
    try { [IO.File]::AppendAllText($LogYolu, ('[{0:yyyy-MM-dd HH:mm:ss}] {1}' -f (Get-Date), $m) + "`r`n", $Utf8) } catch { }
}

function Format-Arg([string]$a) {
    if ($a -eq '') { return '""' }
    if ($a -notmatch '[\s"]') { return $a }
    return '"' + ($a -replace '(\\*)"', '$1$1\"') + '"'
}

function Invoke-Nlm([string[]]$Argumanlar, [string]$Girdi = $null, [int]$ZamanAsimi = 300) {
    $exe = (Get-Command notebooklm -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1).Source
    if (-not $exe) { $exe = Join-Path $env:USERPROFILE '.local\bin\notebooklm.exe' }
    if (-not (Test-Path -LiteralPath $exe)) { throw 'notebooklm bulunamadi (kurulum: RepoKurulum > NotebookLM)' }
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $exe
    $psi.Arguments = (($Argumanlar | ForEach-Object { Format-Arg $_ }) -join ' ')
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardInput = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = $Utf8
    $psi.StandardErrorEncoding = $Utf8
    $psi.EnvironmentVariables['PYTHONUTF8'] = '1'
    $psi.EnvironmentVariables['PYTHONIOENCODING'] = 'utf-8'
    $psi.EnvironmentVariables['NO_COLOR'] = '1'
    $p = [System.Diagnostics.Process]::Start($psi)
    if ($Girdi) {
        $b = $Utf8.GetBytes($Girdi)
        $p.StandardInput.BaseStream.Write($b, 0, $b.Length)
    }
    $p.StandardInput.Close()
    $o = $p.StandardOutput.ReadToEndAsync(); $e = $p.StandardError.ReadToEndAsync()
    if (-not $p.WaitForExit($ZamanAsimi * 1000)) { try { $p.Kill() } catch { }; throw "notebooklm zaman asimi: $($Argumanlar -join ' ')" }
    $p.WaitForExit()
    return @{ Kod = $p.ExitCode; Cikti = $o.Result; Hata = $e.Result }
}

function Read-Durum {
    $d = @{ notebook_id = $null; kaynaklar = @{}; islenen = @{} }
    if (Test-Path -LiteralPath $DurumYolu) {
        try {
            $j = [IO.File]::ReadAllText($DurumYolu, $Utf8) | ConvertFrom-Json
            $d.notebook_id = $j.notebook_id
            if ($j.kaynaklar) { foreach ($p in $j.kaynaklar.PSObject.Properties) { $d.kaynaklar[$p.Name] = $p.Value } }
            if ($j.islenen) { foreach ($p in $j.islenen.PSObject.Properties) { $d.islenen[$p.Name] = [int]$p.Value } }
        } catch { Log "Durum dosyasi okunamadi, yeniden olusturulacak: $($_.Exception.Message)" }
    }
    return $d
}

function Write-Durum($d) {
    # islenen listesini sinirli tut (son 300 oturum)
    if ($d.islenen.Count -gt 300) {
        $fazla = @($d.islenen.Keys | Select-Object -First ($d.islenen.Count - 300))
        foreach ($k in $fazla) { $d.islenen.Remove($k) }
    }
    $o = [ordered]@{
        aciklama    = 'RepoKurulum hafiza durumu. notebook_id: NotebookLM Claude Hafiza notebook kimligi. Claude bu kimlikle sorgu yapar.'
        notebook_id = $d.notebook_id
        kaynaklar   = $d.kaynaklar
        islenen     = $d.islenen
    }
    [IO.File]::WriteAllText($DurumYolu, ($o | ConvertTo-Json -Depth 6), $Utf8)
}

function Get-NotebookId($d) {
    if ($d.notebook_id) { return $d.notebook_id }
    $r = Invoke-Nlm @('list', '--json')
    if ($r.Kod -eq 0) {
        try {
            $l = $r.Cikti | ConvertFrom-Json
            $nb = @($l.notebooks) | Where-Object { $_.title -eq $NotebookAdi } | Select-Object -First 1
            if ($nb) { $d.notebook_id = $nb.id; Log "Mevcut notebook bulundu: $($nb.id)"; return $nb.id }
        } catch { }
    }
    $r = Invoke-Nlm @('create', $NotebookAdi, '--json')
    if ($r.Kod -ne 0) { throw "Notebook olusturulamadi: $($r.Hata)$($r.Cikti)" }
    $id = ($r.Cikti | ConvertFrom-Json).notebook.id
    if (-not $id) { throw "Notebook kimligi okunamadi: $($r.Cikti)" }
    $d.notebook_id = $id
    Log "Notebook olusturuldu: $NotebookAdi ($id)"
    return $id
}

function Protect-Metin([string]$s) {
    # Sirlari maskele (gonderilmeden once)
    $desenler = @(
        'sk-ant-[A-Za-z0-9_\-]{10,}', 'sk-[A-Za-z0-9_\-]{20,}', 'gh[pousr]_[A-Za-z0-9]{20,}', 'github_pat_[A-Za-z0-9_]{20,}',
        'AKIA[0-9A-Z]{16}', 'AIza[0-9A-Za-z_\-]{30,}', 'xox[abpr]-[A-Za-z0-9\-]{10,}', 'ya29\.[A-Za-z0-9_\-]{20,}',
        '(?i)bearer\s+[A-Za-z0-9\._\-]{16,}', '-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----'
    )
    foreach ($d in $desenler) { $s = [regex]::Replace($s, $d, '[GIZLENDI]') }
    # anahtar=deger bicimi: anahtar adi kalsin, deger gizlensin
    $s = [regex]::Replace($s, '(?i)((?:api[_-]?key|token|secret|password|passwd|parola|sifre)\s*[:=]\s*)["'']?[^\s"'',;]{6,}', '$1[GIZLENDI]')
    return $s
}

function Read-Satirlar([string]$Yol) {
    $fs = [IO.File]::Open($Yol, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
    try {
        $sr = New-Object IO.StreamReader($fs, $Utf8)
        $l = New-Object System.Collections.Generic.List[string]
        while ($null -ne ($x = $sr.ReadLine())) { $l.Add($x) }
        return $l
    } finally { $fs.Dispose() }
}

function Kisalt([string]$s, [int]$n) {
    $s = ($s -replace '\s+', ' ').Trim()
    if ($s.Length -gt $n) { return $s.Substring(0, $n) + ' ...' }
    return $s
}

function New-Ozet([System.Collections.Generic.List[string]]$Satirlar, [int]$Bas) {
    $istekler = New-Object System.Collections.Generic.List[string]
    $cevaplar = New-Object System.Collections.Generic.List[string]
    $degisen = New-Object System.Collections.Generic.HashSet[string]
    $okunan = New-Object System.Collections.Generic.HashSet[string]
    $komutlar = New-Object System.Collections.Generic.List[string]
    $araclar = @{}
    for ($i = $Bas; $i -lt $Satirlar.Count; $i++) {
        $s = $Satirlar[$i]
        if ($s.Length -gt 2000000) { continue }
        try { $o = $s | ConvertFrom-Json } catch { continue }
        if ($o.isMeta -or $o.isSidechain) { continue }
        $c = $o.message.content
        if ($o.type -eq 'user') {
            $metinler = @()
            if ($c -is [string]) { $metinler = @($c) }
            else { $metinler = @($c | Where-Object { $_.type -eq 'text' } | ForEach-Object { $_.text }) }
            foreach ($t in $metinler) {
                if (-not $t) { continue }
                $t = [string]$t
                if ($t.TrimStart().StartsWith('<') -or $t -match 'system-reminder|Request interrupted') { continue }
                $istekler.Add((Kisalt $t 600))
            }
        } elseif ($o.type -eq 'assistant') {
            foreach ($p in @($c)) {
                if ($p.type -eq 'text' -and $p.text) { $cevaplar.Add([string]$p.text) }
                elseif ($p.type -eq 'tool_use') {
                    $ad = [string]$p.name
                    $etiket = $ad
                    if ($ad -like 'mcp__*') { $parca = $ad -split '__'; $etiket = ($parca[1] -replace '^plugin_[^_]+_', '') }
                    elseif ($ad -eq 'Skill') { $etiket = 'skill:' + $p.input.skill }
                    elseif ($ad -in @('Agent', 'Task')) { $etiket = 'ajan:' + $p.input.subagent_type }
                    if ($araclar.ContainsKey($etiket)) { $araclar[$etiket]++ } else { $araclar[$etiket] = 1 }
                    $fp = $p.input.file_path; if (-not $fp) { $fp = $p.input.notebook_path }
                    if ($fp) {
                        if ($ad -in @('Edit', 'Write', 'MultiEdit', 'NotebookEdit')) { [void]$degisen.Add([string]$fp) } else { [void]$okunan.Add([string]$fp) }
                    }
                    if ($ad -in @('Bash', 'PowerShell') -and $p.input.command -and $komutlar.Count -lt 15) { $komutlar.Add((Kisalt ([string]$p.input.command) 160)) }
                }
            }
        }
    }
    if ($istekler.Count -eq 0 -and $degisen.Count -eq 0) { return $null }

    $proje = Split-Path -Leaf $Dizin
    try { $u = (& git -C "$Dizin" remote get-url origin 2>$null); if ($u) { $proje = ($u -replace '\.git$', '' -replace '^.*[:/]([^/]+/[^/]+)$', '$1') } } catch { }
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine(('## {0:yyyy-MM-dd HH:mm} | {1} | {2} | oturum {3}' -f (Get-Date), $proje, $Olay, ($Oturum.Substring(0, [Math]::Min(8, $Oturum.Length)))))
    [void]$sb.AppendLine("Klasor: $Dizin")
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine('### Istekler')
    foreach ($t in ($istekler | Select-Object -First 25)) { [void]$sb.AppendLine("- $t") }
    if ($cevaplar.Count -gt 0) {
        [void]$sb.AppendLine(''); [void]$sb.AppendLine('### Son cevap')
        [void]$sb.AppendLine((Kisalt $cevaplar[$cevaplar.Count - 1] 2500))
    }
    if ($degisen.Count -gt 0) { [void]$sb.AppendLine(''); [void]$sb.AppendLine('### Degisen dosyalar'); foreach ($f in ($degisen | Select-Object -First 40)) { [void]$sb.AppendLine("- $f") } }
    if ($okunan.Count -gt 0) { [void]$sb.AppendLine(''); [void]$sb.AppendLine('### Okunan dosyalar'); foreach ($f in ($okunan | Select-Object -First 25)) { [void]$sb.AppendLine("- $f") } }
    if ($komutlar.Count -gt 0) { [void]$sb.AppendLine(''); [void]$sb.AppendLine('### Calistirilan komutlar'); foreach ($k in $komutlar) { [void]$sb.AppendLine("- $k") } }
    if ($araclar.Count -gt 0) {
        $liste = ($araclar.GetEnumerator() | Sort-Object Value -Descending | ForEach-Object { "$($_.Key) ($($_.Value))" }) -join ', '
        [void]$sb.AppendLine(''); [void]$sb.AppendLine('### Kullanilan araclar'); [void]$sb.AppendLine($liste)
    }
    [void]$sb.AppendLine('')
    return (Protect-Metin $sb.ToString())
}

function Send-Metin($d, [string]$Metin) {
    $nb = Get-NotebookId $d
    $ay = (Get-Date).ToString('yyyy-MM')
    $src = $d.kaynaklar[$ay]
    if ($src) {
        $r = Invoke-Nlm @('source', 'append', $src, '-', '-n', $nb, '--json') $Metin
        if ($r.Kod -eq 0) { return }
        if (($r.Hata + $r.Cikti) -notmatch '(?i)not found|no source|does not exist|bulunamad|NOT_FOUND') {
            throw "Ekleme basarisiz (sonra tekrar denenecek): $($r.Hata)$($r.Cikti)"
        }
        Log "Aylik kaynak bulunamadi (silinmis olabilir), yenisi acilacak"
        $d.kaynaklar.Remove($ay)
    }
    $baslik = "$NotebookAdi $ay"
    $r = Invoke-Nlm @('source', 'add', '-', '--type', 'text', '--title', $baslik, '-n', $nb, '--json') ("# $baslik`n`nClaude Code oturum ozetleri (otomatik).`n`n" + $Metin)
    if ($r.Kod -ne 0) { throw "Kaynak eklenemedi: $($r.Hata)$($r.Cikti)" }
    $id = ($r.Cikti | ConvertFrom-Json).source.id
    if (-not $id) { throw "Kaynak kimligi okunamadi: $($r.Cikti)" }
    $d.kaynaklar[$ay] = $id
    Log "Yeni aylik kaynak: $baslik ($id)"
}

# ------------------------------------------------------------------ Calisma modlari
if ($Hazirla) {
    try {
        $d = Read-Durum
        $id = Get-NotebookId $d
        Write-Durum $d
        Write-Output "Claude Hafiza notebook hazir: $id"
        exit 0
    } catch { Log "Hazirla hatasi: $($_.Exception.Message)"; Write-Output "HATA: $($_.Exception.Message)"; exit 1 }
}

if (-not $Arkaplan) {
    # Hook modu: stdin'deki JSON'u oku, isi arka plana devret, hemen don
    try {
        $ham = [Console]::In.ReadToEnd()
        $h = $ham | ConvertFrom-Json
        if (-not $h.transcript_path) { exit 0 }
        $q = { param($s) '"' + ([string]$s -replace '"', '') + '"' }
        $arg = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ' + (& $q $PSCommandPath) + ' -Arkaplan' +
            ' -Transkript ' + (& $q $h.transcript_path) + ' -Oturum ' + (& $q $h.session_id) +
            ' -Dizin ' + (& $q $h.cwd) + ' -Olay ' + (& $q $h.hook_event_name)
        Start-Process -FilePath 'powershell.exe' -ArgumentList $arg -WindowStyle Hidden | Out-Null
    } catch { Log "Hook hatasi: $($_.Exception.Message)" }
    exit 0
}

# Arka plan modu: tek seferde tek is (PreCompact ve SessionEnd ust uste gelebilir)
$kilit = New-Object System.Threading.Mutex($false, 'Local\RepoKurulumHafiza')
try { [void]$kilit.WaitOne(600000) } catch { }
try {
    $d = Read-Durum
    # 1) Daha once gonderilemeyenler
    foreach ($f in @(Get-ChildItem -LiteralPath $Bekleyen -Filter *.md -ErrorAction SilentlyContinue | Sort-Object Name)) {
        try { Send-Metin $d ([IO.File]::ReadAllText($f.FullName, $Utf8)); Remove-Item -LiteralPath $f.FullName -Force; Log "Bekleyen gonderildi: $($f.Name)" }
        catch { Log "Bekleyen hala gonderilemiyor: $($_.Exception.Message)"; break }
    }
    # 2) Bu oturumun yeni kismi
    if ($Transkript -and (Test-Path -LiteralPath $Transkript)) {
        $satirlar = Read-Satirlar $Transkript
        $bas = 0
        if ($d.islenen.ContainsKey($Oturum)) { $bas = [int]$d.islenen[$Oturum] }
        if ($satirlar.Count -gt $bas) {
            $ozet = New-Ozet $satirlar $bas
            $d.islenen[$Oturum] = $satirlar.Count
            if ($ozet) {
                try { Send-Metin $d $ozet; Log "Oturum ozeti eklendi ($Olay, $Oturum, satir $bas-$($satirlar.Count))" }
                catch {
                    $dosya = Join-Path $Bekleyen ('{0:yyyyMMdd_HHmmss}_{1}.md' -f (Get-Date), ($Oturum -replace '[^A-Za-z0-9\-]', ''))
                    [IO.File]::WriteAllText($dosya, $ozet, $Utf8)
                    Log "Gonderilemedi, bekleyene yazildi: $($_.Exception.Message)"
                }
            }
        }
    }
    Write-Durum $d
} catch { Log "Arka plan hatasi: $($_.Exception.Message)" }
finally { try { $kilit.ReleaseMutex() } catch { } }
exit 0
