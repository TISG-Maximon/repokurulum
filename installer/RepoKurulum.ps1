#Requires -Version 5.1
<#
.SYNOPSIS
  RepoKurulum - Claude Code + MCP + skill kurulum uygulamasi (pencereli veya sessiz).

.DESCRIPTION
  Bilesenler installer\bilesenler.json dosyasindan okunur. Her bilesen icin:
    1) "kontrol" ile kurulu mu bakilir (kuruluysa atlanir -> tekrar calistirmak guvenli)
    2) "kur" icindeki yontemler sirayla denenir; biri basarili olunca durulur
    3) "sonra" adimlari calistirilir
  Hicbir adim yonetici izni istemez; winget gerekiyorsa UAC penceresini kendisi acar.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -STA -File RepoKurulum.ps1
  powershell -ExecutionPolicy Bypass -File RepoKurulum.ps1 -Sessiz
  powershell -ExecutionPolicy Bypass -File RepoKurulum.ps1 -Sessiz -Bilesenler "claude,playwright-mcp,graphify"
  powershell -ExecutionPolicy Bypass -File RepoKurulum.ps1 -Liste
#>
[CmdletBinding()]
param(
    [switch]$Sessiz,
    [string]$Bilesenler = '',
    [switch]$Liste,
    [switch]$Zorla,
    [switch]$Kurallar,
    [switch]$TumKurallar,
    [switch]$GuncellemeKontrol,
    [switch]$Guncelle,
    [string]$Yapilandirma = ''
)

$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
} catch { }

if (-not $Yapilandirma) { $Yapilandirma = Join-Path $PSScriptRoot 'bilesenler.json' }
# Repo kok dizini (installer klasorunun bir ustu); -File veya scriptblock ile calismada da dogru
$script:Kok = Split-Path -Parent (Split-Path -Parent ([IO.Path]::GetFullPath($Yapilandirma)))

# ------------------------------------------------------------------ Durum
$script:LogBox      = $null
$script:DurumEtiketi = $null
$script:ListView    = $null
$script:McpOnbellek = $null
$script:PluginCikti = $null
$script:SonCikti    = ''
$script:Gizliler    = @{}
$script:Hatalar     = 0

$LogDir = Join-Path $env:LOCALAPPDATA 'RepoKurulum\logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir ('kurulum_{0:yyyyMMdd_HHmmss}.log' -f (Get-Date))

# ------------------------------------------------------------------ Yardimcilar
function Invoke-UiPump {
    if ($script:LogBox) { [System.Windows.Forms.Application]::DoEvents() }
}

function Write-Log {
    param([string]$Mesaj, [ValidateSet('BILGI', 'OK', 'UYARI', 'HATA')][string]$Seviye = 'BILGI')
    $satir = '[{0:HH:mm:ss}] [{1}] {2}' -f (Get-Date), $Seviye, $Mesaj
    try { Add-Content -LiteralPath $LogFile -Value $satir -Encoding UTF8 } catch { }
    if ($script:LogBox) {
        $script:LogBox.AppendText($satir + [Environment]::NewLine)
        Invoke-UiPump
    } else {
        $renk = @{ BILGI = 'Gray'; OK = 'Green'; UYARI = 'Yellow'; HATA = 'Red' }[$Seviye]
        Write-Host $satir -ForegroundColor $renk
    }
}

function Update-EnvPath {
    $parcalar = @(
        [Environment]::GetEnvironmentVariable('Path', 'Machine'),
        [Environment]::GetEnvironmentVariable('Path', 'User'),
        (Join-Path $env:USERPROFILE '.local\bin'),
        (Join-Path $env:APPDATA 'npm'),
        (Join-Path $env:ProgramFiles 'nodejs'),
        (Join-Path $env:ProgramFiles 'Git\cmd'),
        (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links')
    ) | Where-Object { $_ }
    $env:Path = ($parcalar -join ';')
}

function Test-Komut([string]$Ad) {
    return [bool](Get-Command $Ad -ErrorAction SilentlyContinue)
}

function Format-Arguman([string]$Arg) {
    if ($Arg -eq '') { return '""' }
    if ($Arg -notmatch '[\s"]') { return $Arg }
    return '"' + ($Arg -replace '(\\*)"', '$1$1\"') + '"'
}

function Stop-ProcessTree([int]$ProcessId) {
    try { & taskkill.exe /T /F /PID $ProcessId 2>&1 | Out-Null } catch { }
}

function Invoke-Harici {
    <# Dis komut calistirir; ciktiyi log'a yazar; arayuzu dondurmaz; stdin hemen kapatilir. #>
    param([string]$Dosya, [string[]]$Argumanlar = @(), [int]$ZamanAsimi = 900, [switch]$Sessizce)

    # .ps1 sarmalayicilari (npx.ps1, npm.ps1) Process.Start ile calismaz -> sadece Application
    $komut = Get-Command $Dosya -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $komut) { Write-Log "Komut bulunamadi: $Dosya" 'HATA'; return 9009 }
    $yol = $komut.Source
    if (-not $yol) { $yol = $komut.Name }

    $argMetni = ($Argumanlar | ForEach-Object { Format-Arguman $_ }) -join ' '
    # .cmd/.bat dosyalari (npm, npx, npm ile kurulan claude) dogrudan baslatilamaz -> cmd /c
    if ($yol -match '\.(cmd|bat)$') {
        $argMetni = '/d /s /c "' + (Format-Arguman $yol) + ' ' + $argMetni + '"'
        $yol = $env:ComSpec
    }
    if (-not $Sessizce) { Write-Log ("> {0} {1}" -f $Dosya, (($Argumanlar | ForEach-Object { Format-Arguman $_ }) -join ' ')) }

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $yol
    $psi.Arguments = $argMetni
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.RedirectStandardInput = $true
    try {
        $p = [System.Diagnostics.Process]::Start($psi)
    } catch {
        Write-Log "Baslatilamadi: $Dosya - $($_.Exception.Message)" 'HATA'
        return 9009
    }
    try { $p.StandardInput.Close() } catch { }
    $outTask = $p.StandardOutput.ReadToEndAsync()
    $errTask = $p.StandardError.ReadToEndAsync()
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    # Uzun adimlarda "devam ediyor" gostergesi: pencerede donen simge + sure, logda her 20 sn bir satir
    $isim = $Dosya
    if ($Argumanlar.Count -gt 0) { $isim = $Dosya + ' ' + (($Argumanlar | Select-Object -First 3) -join ' ') }
    $sonNabiz = 0
    $simgeler = '|/-\'
    while (-not $p.HasExited) {
        Invoke-UiPump
        Start-Sleep -Milliseconds 150
        $sn = [int]$sw.Elapsed.TotalSeconds
        if ($script:DurumEtiketi) {
            $simge = $simgeler[[int]($sw.ElapsedMilliseconds / 250) % 4]
            $script:DurumEtiketi.Text = ('  {0}  Calisiyor ({1:mm\:ss}):  {2}' -f $simge, $sw.Elapsed, $isim)
        }
        if (-not $Sessizce -and $sn -ge ($sonNabiz + 20)) {
            $sonNabiz = $sn
            if ($sn -ge 300) {
                Write-Log ("... hala devam ediyor ({0} dk) - buyuk indirme veya yavas internet olabilir; en fazla {1} dk beklenir" -f [int]($sn / 60), [int]($ZamanAsimi / 60))
            } else {
                Write-Log ("... devam ediyor ({0} sn) - takilmadi, bekleniyor" -f $sn)
            }
        }
        if ($sw.Elapsed.TotalSeconds -gt $ZamanAsimi) {
            Write-Log "Zaman asimi ($ZamanAsimi sn): $Dosya - durduruluyor" 'UYARI'
            Stop-ProcessTree $p.Id
            break
        }
    }
    try { $p.WaitForExit(5000) | Out-Null } catch { }
    if ($script:DurumEtiketi) { $script:DurumEtiketi.Text = '  Hazir' }
    $cikti = ''
    try { $cikti = $outTask.Result + $errTask.Result } catch { }
    $script:SonCikti = $cikti
    if ($cikti -and $cikti.Trim()) {
        try { Add-Content -LiteralPath $LogFile -Value $cikti.TrimEnd() -Encoding UTF8 } catch { }
    }
    $kod = 1
    try { $kod = $p.ExitCode } catch { }
    return $kod
}

function Expand-Deger([string]$Metin) {
    if ($null -eq $Metin) { return '' }
    $sonuc = [Environment]::ExpandEnvironmentVariables($Metin)
    foreach ($k in @($script:Gizliler.Keys)) {
        $sonuc = $sonuc.Replace('{' + $k + '}', [string]$script:Gizliler[$k])
    }
    return $sonuc
}

# ------------------------------------------------------------------ Gizli anahtarlar
function Get-GizliDeger([string]$Ad) {
    if ($script:Gizliler.ContainsKey($Ad) -and $script:Gizliler[$Ad]) { return $script:Gizliler[$Ad] }
    foreach ($kapsam in 'Process', 'User') {
        $v = [Environment]::GetEnvironmentVariable($Ad, $kapsam)
        if ($v) { $script:Gizliler[$Ad] = $v; return $v }
    }
    return $null
}

function Request-Gizli($Gizli, [string]$BilesenAdi) {
    $mevcut = Get-GizliDeger $Gizli.ad
    if ($mevcut) { return $true }
    if (-not $script:LogBox) {
        Write-Log "$BilesenAdi atlandi: $($Gizli.ad) ortam degiskeni tanimli degil ($($Gizli.url))" 'UYARI'
        return $false
    }
    $f = New-Object System.Windows.Forms.Form
    $f.Text = "Anahtar gerekli: $($Gizli.ad)"
    $f.Size = New-Object System.Drawing.Size(520, 230)
    $f.StartPosition = 'CenterParent'
    $f.FormBorderStyle = 'FixedDialog'
    $f.MaximizeBox = $false; $f.MinimizeBox = $false
    $l = New-Object System.Windows.Forms.Label
    $l.Text = "$BilesenAdi icin $($Gizli.ad) gerekli.`r`nAnahtari buradan alabilirsin:"
    $l.SetBounds(12, 12, 480, 36)
    $link = New-Object System.Windows.Forms.LinkLabel
    $link.Text = $Gizli.url
    $link.SetBounds(12, 50, 480, 20)
    $link.add_LinkClicked({ param($s, $e) Start-Process $s.Text })
    $t = New-Object System.Windows.Forms.TextBox
    $t.SetBounds(12, 76, 480, 24)
    $t.UseSystemPasswordChar = $true
    $c = New-Object System.Windows.Forms.CheckBox
    $c.Text = 'Kullanici ortam degiskeni olarak kalici kaydet'
    $c.Checked = $true
    $c.SetBounds(12, 106, 480, 22)
    $ok = New-Object System.Windows.Forms.Button
    $ok.Text = 'Tamam'; $ok.DialogResult = 'OK'; $ok.SetBounds(316, 140, 85, 28)
    $iptal = New-Object System.Windows.Forms.Button
    $iptal.Text = 'Atla'; $iptal.DialogResult = 'Cancel'; $iptal.SetBounds(407, 140, 85, 28)
    $f.Controls.AddRange(@($l, $link, $t, $c, $ok, $iptal))
    $f.AcceptButton = $ok; $f.CancelButton = $iptal
    $sonuc = $f.ShowDialog()
    $deger = $t.Text.Trim()
    $kalici = $c.Checked
    $f.Dispose()
    if ($sonuc -ne 'OK' -or -not $deger) {
        Write-Log "$BilesenAdi atlandi: anahtar girilmedi" 'UYARI'
        return $false
    }
    $script:Gizliler[$Gizli.ad] = $deger
    if ($kalici) { [Environment]::SetEnvironmentVariable($Gizli.ad, $deger, 'User') }
    return $true
}

# ------------------------------------------------------------------ Kontroller
function Get-McpListesi {
    if ($null -ne $script:McpOnbellek) { return $script:McpOnbellek }
    $adlar = @()
    $dosya = Join-Path $env:USERPROFILE '.claude.json'
    $okundu = $false
    if (Test-Path -LiteralPath $dosya) {
        try {
            $json = Get-Content -LiteralPath $dosya -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($json.mcpServers) { $adlar = @($json.mcpServers.PSObject.Properties.Name) }
            $okundu = $true
        } catch { $okundu = $false }
    } else { $okundu = $true }
    if (-not $okundu -and (Test-Komut 'claude')) {
        # .claude.json PowerShell 5.1 ile okunamadiysa (buyuk/kucuk harf cakismasi vb.) CLI'ye sor
        Invoke-Harici 'claude' @('mcp', 'list') -ZamanAsimi 120 -Sessizce | Out-Null
        $adlar = @([regex]::Matches($script:SonCikti, '(?m)^([A-Za-z0-9_.\-]+):\s') | ForEach-Object { $_.Groups[1].Value })
    }
    $script:McpOnbellek = $adlar
    return $adlar
}

function Test-Plugin([string]$Ad) {
    if (-not (Test-Komut 'claude')) { return $false }
    if ($null -eq $script:PluginCikti) {
        Invoke-Harici 'claude' @('plugin', 'list') -ZamanAsimi 120 -Sessizce | Out-Null
        $script:PluginCikti = [string]$script:SonCikti
    }
    return ($script:PluginCikti -match ('(?im)\b' + [regex]::Escape($Ad) + '\b'))
}

function Reset-Onbellek { $script:McpOnbellek = $null; $script:PluginCikti = $null }

# ------------------------------------------------------------------ ~/.claude/settings.json
function Get-AyarYolu { return (Join-Path $env:USERPROFILE '.claude\settings.json') }

function Read-Ayarlar {
    # Gecersiz JSON'da hata firlatir (cagiran yakalar; dosyaya dokunulmaz)
    $yol = Get-AyarYolu
    if (-not (Test-Path -LiteralPath $yol)) { return (New-Object PSObject) }
    $metin = [IO.File]::ReadAllText($yol, [Text.Encoding]::UTF8)
    if (-not $metin.Trim()) { return (New-Object PSObject) }
    return ($metin | ConvertFrom-Json -ErrorAction Stop)
}

function Get-AyarDegeri($Ayar, [string]$Anahtar) {
    $o = $Ayar
    foreach ($p in $Anahtar.Split('.')) { if ($null -eq $o) { return $null }; $o = $o.$p }
    return $o
}

function ConvertTo-GenisDeger($D, [bool]$Egik) {
    # Dizelerdeki %DEGISKEN% ve {GIZLI} degerlerini acar; istenirse \ -> / yapar (Git Bash icin)
    if ($D -is [string]) {
        $x = Expand-Deger $D
        if ($Egik) { $x = $x.Replace('\', '/') }
        return $x
    }
    if ($D -is [System.Management.Automation.PSCustomObject]) {
        $y = New-Object PSObject
        foreach ($p in $D.PSObject.Properties) { $y | Add-Member -NotePropertyName $p.Name -NotePropertyValue (ConvertTo-GenisDeger $p.Value $Egik) }
        return $y
    }
    return $D
}

function Test-DosyalarGuncel($B) {
    # Bilesenin kurdugu (isaretli) dosyalar repodaki surumle ayni mi? Degilse guncelleme gerekir.
    foreach ($yontem in @($B.kur)) {
        foreach ($a in @($yontem)) {
            if ($a.tur -ne 'dosya-kopyala') { continue }
            $kaynak = Join-Path $script:Kok $a.kaynak
            $hedef = Expand-Deger $a.hedef
            if (-not (Test-Path -LiteralPath $kaynak) -or -not (Test-Path -LiteralPath $hedef)) { continue }
            $hedefMetin = [IO.File]::ReadAllText($hedef)
            if ($hedefMetin -notmatch 'repokurulum') { continue }   # kullanici sahiplenmis, dokunma
            if ((Get-FileHash -LiteralPath $kaynak).Hash -ne (Get-FileHash -LiteralPath $hedef).Hash) { return $false }
        }
    }
    return $true
}

function Test-Bilesen($B) {
    if (-not (Test-BilesenTemel $B)) { return $false }
    return (Test-DosyalarGuncel $B)
}

function Test-BilesenTemel($B) {
    $k = $B.kontrol
    if (-not $k) { return $false }
    if ($k.komut) { return (Test-Komut $k.komut) }
    if ($k.dosya) {
        foreach ($d in @($k.dosya)) {
            if (Test-Path -LiteralPath ([Environment]::ExpandEnvironmentVariables($d))) { return $true }
        }
        return $false
    }
    if ($k.mcp) { return (@(Get-McpListesi) -contains $k.mcp) }
    if ($k.plugin) { return (Test-Plugin $k.plugin) }
    if ($k.ortam) { return [bool][Environment]::GetEnvironmentVariable($k.ortam, 'User') }
    if ($k.hook) {
        try { $liste = Get-AyarDegeri (Read-Ayarlar) ('hooks.' + $k.hook.olay) } catch { return $false }
        foreach ($g in @($liste)) { foreach ($h in @($g.hooks)) { if ([string]$h.command -like ('*' + $k.hook.icerir + '*')) { return $true } } }
        return $false
    }
    if ($k.ayar) {
        try { $v = Get-AyarDegeri (Read-Ayarlar) $k.ayar.anahtar } catch { return $false }
        if ($null -eq $v) { return $false }
        return ([string]$v -like ('*' + $k.ayar.icerir + '*'))
    }
    return $false
}

# ------------------------------------------------------------------ Adimlar
function Resolve-McpKomut([string[]]$Komut) {
    $ilk = $Komut[0]
    $geri = @()
    if ($Komut.Count -gt 1) { $geri = $Komut[1..($Komut.Count - 1)] }
    $c = Get-Command $ilk -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($c -and $c.Source -and $c.Source -match '\.(cmd|bat)$') {
        # Windows kurali: npx/npm gibi .cmd'ler MCP icin "cmd /c" ile sarilir
        return @('cmd', '/c', $ilk) + $geri
    }
    if ($ilk -in @('npx', 'npm')) { return @('cmd', '/c', $ilk) + $geri }
    if ($c -and $c.Source) { return @($c.Source) + $geri }   # tam yol: PATH sorunlarini onler
    return $Komut
}

function Invoke-Adim($A) {
    switch ($A.tur) {
        'winget' {
            if (-not (Test-Komut 'winget')) {
                Write-Log "winget yok (Microsoft Store > 'App Installer'). $($A.id) bu yontemle kurulamadi." 'UYARI'
                return 1
            }
            $wargs = @('install', '--id', $A.id, '-e', '--source', 'winget', '--silent',
                '--accept-package-agreements', '--accept-source-agreements', '--disable-interactivity')
            $kod = Invoke-Harici 'winget' $wargs
            # -1978335189 = zaten kurulu ; -1978335135 = guncelleme yok
            if ($kod -in @(0, -1978335189, -1978335135)) { return 0 }
            # Indirme/ag hatasi (HTTP 5xx, baglanti kesildi vb.) -> 10 sn sonra bir kez daha dene
            $agHatasi = (($kod -band 0xFFFF0000) -eq 0x80190000) -or (($kod -band 0xFFFF0000) -eq 0x80070000 -and $script:SonCikti -match '(?i)download|network|timeout') -or ($script:SonCikti -match '(?i)download fail|network|0x8019|0x80072|timeout|zaman asimi')
            if ($kod -ne 0 -and $agHatasi) {
                Write-Log "Indirme hatasi, 10 sn sonra tekrar deneniyor: $($A.id)" 'UYARI'
                for ($i = 0; $i -lt 66; $i++) { Invoke-UiPump; Start-Sleep -Milliseconds 150 }
                $kod = Invoke-Harici 'winget' $wargs
                if ($kod -in @(0, -1978335189, -1978335135)) { return 0 }
            }
            return $kod
        }
        'ps' {
            return (Invoke-Harici 'powershell.exe' @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', (Expand-Deger $A.komut)))
        }
        'calistir' {
            Update-EnvPath
            $argumanlar = @($A.argumanlar | ForEach-Object { Expand-Deger $_ })
            $za = 900
            if ($A.zaman_asimi) { $za = [int]$A.zaman_asimi }
            $kod = Invoke-Harici $A.dosya $argumanlar -ZamanAsimi $za
            if ($A.ciktiyi_goster -and $script:SonCikti) {
                $ozet = (([string]$script:SonCikti -split "`n") | Where-Object { $_.Trim() } | Select-Object -Last 3) -join ' / '
                Write-Log ("Cikti: " + $ozet)
            }
            return $kod
        }
        'uvtool' {
            Update-EnvPath
            $py = '3.12'
            if ($A.python) { $py = $A.python }
            $kod = Invoke-Harici 'uv' @('tool', 'install', '--python', $py, $A.paket)
            if ($kod -ne 0 -and $script:SonCikti -match 'already installed') { $kod = 0 }
            Invoke-Harici 'uv' @('tool', 'update-shell') -Sessizce | Out-Null
            Update-EnvPath
            return $kod
        }
        'ortam' {
            [Environment]::SetEnvironmentVariable($A.ad, $A.deger, 'User')
            Set-Item -Path ("Env:" + $A.ad) -Value $A.deger
            Write-Log "Ortam degiskeni: $($A.ad)=$($A.deger)"
            return 0
        }
        'mcp' {
            Update-EnvPath
            if (-not (Test-Komut 'claude')) { Write-Log 'claude yok, MCP eklenemez' 'HATA'; return 1 }
            $komut = Resolve-McpKomut @($A.komut)
            if ($A.komut[0] -eq 'npx') {
                Write-Log "Paket onbellege indiriliyor: $($A.komut -join ' ')"
                Invoke-Harici 'npx' (@($A.komut[1..($A.komut.Count - 1)]) + '--help') -ZamanAsimi 240 -Sessizce | Out-Null
            }
            Invoke-Harici 'claude' @('mcp', 'remove', $A.ad, '-s', 'user') -Sessizce | Out-Null
            $argumanlar = @('mcp', 'add', '-s', 'user', $A.ad)
            if ($A.ortam) {
                foreach ($p in $A.ortam.PSObject.Properties) { $argumanlar += @('-e', ($p.Name + '=' + (Expand-Deger $p.Value))) }
            }
            $argumanlar += '--'
            $argumanlar += $komut
            $kod = Invoke-Harici 'claude' $argumanlar -Sessizce
            Write-Log ("> claude mcp add -s user {0} -- {1}" -f $A.ad, ($komut -join ' '))
            Reset-Onbellek
            return $kod
        }
        'mcp-http' {
            if (-not (Test-Komut 'claude')) { Write-Log 'claude yok, MCP eklenemez' 'HATA'; return 1 }
            Invoke-Harici 'claude' @('mcp', 'remove', $A.ad, '-s', 'user') -Sessizce | Out-Null
            $argumanlar = @('mcp', 'add', '-s', 'user', '--transport', 'http', $A.ad, $A.url)
            foreach ($h in @($A.basliklar)) { if ($h) { $argumanlar += @('-H', (Expand-Deger $h)) } }
            $kod = Invoke-Harici 'claude' $argumanlar -Sessizce
            Write-Log "> claude mcp add -s user --transport http $($A.ad) $($A.url) (basliklar gizlendi)"
            Reset-Onbellek
            return $kod
        }
        'ayar' {
            # ~/.claude/settings.json icine tek bir anahtar yazar; diger ayarlara dokunmaz, ilk seferde yedek alir
            try { $ayar = Read-Ayarlar } catch {
                Write-Log ("settings.json okunamadi (gecersiz JSON?), DEGISTIRILMEDI: " + (Get-AyarYolu)) 'HATA'
                return 1
            }
            $deger = ConvertTo-GenisDeger $A.deger ([bool]$A.egik_cizgi)
            $yol = Get-AyarYolu
            New-Item -ItemType Directory -Force -Path (Split-Path $yol) | Out-Null
            $yedek = $yol + '.repokurulum.bak'
            if ((Test-Path -LiteralPath $yol) -and -not (Test-Path -LiteralPath $yedek)) { Copy-Item -LiteralPath $yol -Destination $yedek }
            if ($ayar.PSObject.Properties[$A.anahtar]) { $ayar.($A.anahtar) = $deger }
            else { $ayar | Add-Member -NotePropertyName $A.anahtar -NotePropertyValue $deger }
            [IO.File]::WriteAllText($yol, ($ayar | ConvertTo-Json -Depth 32), (New-Object System.Text.UTF8Encoding($false)))
            Write-Log "settings.json: '$($A.anahtar)' ayarlandi"
            return 0
        }
        'hook-ekle' {
            # settings.json hooks.<olay> listesine komut ekler; ayni isaretli komut varsa gunceller, digerlerine dokunmaz
            try { $ayar = Read-Ayarlar } catch { Write-Log ("settings.json okunamadi, DEGISTIRILMEDI: " + (Get-AyarYolu)) 'HATA'; return 1 }
            $komut = ConvertTo-GenisDeger $A.komut ([bool]$A.egik_cizgi)
            if (-not $ayar.PSObject.Properties['hooks']) { $ayar | Add-Member -NotePropertyName hooks -NotePropertyValue (New-Object PSObject) }
            $grup = @()
            if ($ayar.hooks.PSObject.Properties[$A.olay]) { $grup = @($ayar.hooks.($A.olay)) }
            $yeni = @()
            foreach ($g in $grup) {
                $kalan = @(@($g.hooks) | Where-Object { [string]$_.command -notlike ('*' + $A.isaret + '*') })
                if ($kalan.Count -gt 0) { $g.hooks = $kalan; $yeni += $g }
            }
            $h = [pscustomobject]@{ type = 'command'; command = $komut; timeout = 30 }
            # Istege bagli ek hook ozellikleri (orn. asyncRewake, timeout)
            if ($A.ozellikler) { foreach ($p in $A.ozellikler.PSObject.Properties) { $h | Add-Member -NotePropertyName $p.Name -NotePropertyValue $p.Value -Force } }
            $grupYeni = [pscustomobject]@{ hooks = @($h) }
            if ($A.matcher) { $grupYeni = [pscustomobject]@{ matcher = $A.matcher; hooks = @($h) } }
            $yeni += $grupYeni
            if ($ayar.hooks.PSObject.Properties[$A.olay]) { $ayar.hooks.($A.olay) = $yeni }
            else { $ayar.hooks | Add-Member -NotePropertyName $A.olay -NotePropertyValue $yeni }
            $yol = Get-AyarYolu
            New-Item -ItemType Directory -Force -Path (Split-Path $yol) | Out-Null
            $yedek = $yol + '.repokurulum.bak'
            if ((Test-Path -LiteralPath $yol) -and -not (Test-Path -LiteralPath $yedek)) { Copy-Item -LiteralPath $yol -Destination $yedek }
            [IO.File]::WriteAllText($yol, ($ayar | ConvertTo-Json -Depth 32), (New-Object System.Text.UTF8Encoding($false)))
            Write-Log "settings.json: '$($A.olay)' hook'u eklendi"
            return 0
        }
        'izin-ekle' {
            # settings.json permissions.allow listesine kural ekler (yoksa); digerlerine dokunmaz
            try { $ayar = Read-Ayarlar } catch { Write-Log ("settings.json okunamadi, DEGISTIRILMEDI: " + (Get-AyarYolu)) 'HATA'; return 1 }
            if (-not $ayar.PSObject.Properties['permissions']) { $ayar | Add-Member -NotePropertyName permissions -NotePropertyValue (New-Object PSObject) }
            $liste = @()
            if ($ayar.permissions.PSObject.Properties['allow']) { $liste = @($ayar.permissions.allow) }
            foreach ($kural in @($A.kurallar)) { if ($liste -notcontains $kural) { $liste += $kural } }
            if ($ayar.permissions.PSObject.Properties['allow']) { $ayar.permissions.allow = $liste }
            else { $ayar.permissions | Add-Member -NotePropertyName allow -NotePropertyValue $liste }
            $yol = Get-AyarYolu
            New-Item -ItemType Directory -Force -Path (Split-Path $yol) | Out-Null
            $yedek = $yol + '.repokurulum.bak'
            if ((Test-Path -LiteralPath $yol) -and -not (Test-Path -LiteralPath $yedek)) { Copy-Item -LiteralPath $yol -Destination $yedek }
            [IO.File]::WriteAllText($yol, ($ayar | ConvertTo-Json -Depth 32), (New-Object System.Text.UTF8Encoding($false)))
            Write-Log ("settings.json izin eklendi: " + (@($A.kurallar) -join ', '))
            return 0
        }
        'dosya-kopyala' {
            # Repodaki bir dosyayi kopyalar. Hedef kullaniciya aitse (icinde 'repokurulum' isareti yoksa) dokunmaz.
            $kaynak = Join-Path $script:Kok $A.kaynak
            $hedef = Expand-Deger $A.hedef
            if (-not (Test-Path -LiteralPath $kaynak)) { Write-Log "Kaynak dosya yok: $kaynak" 'HATA'; return 1 }
            if ((Test-Path -LiteralPath $hedef) -and -not ([IO.File]::ReadAllText($hedef) -match 'repokurulum')) {
                Write-Log "Hedef dosya sana ait (isaret yok), dokunulmadi: $hedef" 'UYARI'
                return 0
            }
            New-Item -ItemType Directory -Force -Path (Split-Path $hedef) | Out-Null
            Copy-Item -LiteralPath $kaynak -Destination $hedef -Force
            Write-Log "Dosya kuruldu: $hedef"
            return 0
        }
        default {
            Write-Log "Bilinmeyen adim turu: $($A.tur)" 'HATA'
            return 1
        }
    }
}

function Install-Bilesen($B) {
    Write-Log "==== $($B.ad) ===="
    if ($Zorla -and $B.kontrol.mcp) {
        Invoke-Harici 'claude' @('mcp', 'remove', $B.kontrol.mcp, '-s', 'user') -Sessizce | Out-Null
        Reset-Onbellek
    } elseif ($script:Guncellemeler.ContainsKey($B.id) -and (Test-BilesenTemel $B)) {
        return (Invoke-Guncelleme $B)
    } elseif (Test-Bilesen $B) {
        Write-Log "$($B.ad) zaten kurulu" 'OK'
        return 'Kurulu'
    }
    foreach ($g in @($B.gizli)) {
        if ($g -and -not (Request-Gizli $g $B.ad)) { return 'Atlandi' }
    }
    $sira = 0
    foreach ($yontem in @($B.kur)) {
        $sira++
        if ($sira -gt 1) { Write-Log "Alternatif yontem deneniyor ($sira)..." 'UYARI' }
        foreach ($adim in @($yontem)) {
            $kod = Invoke-Adim $adim
            if ($kod -ne 0) { Write-Log "Adim basarisiz (cikis kodu $kod)" 'UYARI'; break }
        }
        Update-EnvPath
        Reset-Onbellek
        if (Test-Bilesen $B) {
            foreach ($adim in @($B.sonra)) { if ($adim) { Invoke-Adim $adim | Out-Null } }
            Write-Log "$($B.ad) kuruldu" 'OK'
            if ($B.kurulum_notu) { Write-Log ('NOT: ' + [Environment]::ExpandEnvironmentVariables($B.kurulum_notu)) 'UYARI' }
            return 'Kuruldu'
        }
    }
    $script:Hatalar++
    Write-Log "$($B.ad) KURULAMADI. Ayrinti: $LogFile" 'HATA'
    return 'Hata'
}

# ------------------------------------------------------------------ Yapilandirma
if (-not (Test-Path -LiteralPath $Yapilandirma)) {
    Write-Host "Yapilandirma bulunamadi: $Yapilandirma" -ForegroundColor Red
    exit 2
}
$Config = Get-Content -LiteralPath $Yapilandirma -Raw -Encoding UTF8 | ConvertFrom-Json
$Tum = @($Config.bilesenler)
$IdTablo = @{}
foreach ($b in $Tum) { $IdTablo[$b.id] = $b }

function Get-KuralMetni([switch]$Hepsi) {
    <# CLAUDE.md'ye yapistirilacak arac secim kurallari. Varsayilan: sadece KURULU araclar.
       Hicbir dosyaya yazmaz; metni dondurur. #>
    $nl = "`n"
    $satirlar = New-Object System.Collections.Generic.List[string]
    $satirlar.Add('# ' + $Config.kural_basligi)
    $satirlar.Add('')
    foreach ($g in @($Config.genel_kurallar)) { $satirlar.Add('- ' + $g) }
    $satirlar.Add('')
    $kurallar = @()
    foreach ($b in $Tum) {
        if (-not $b.kurallar) { continue }
        if (-not $Hepsi -and -not (Test-Bilesen $b)) { continue }
        foreach ($k in @($b.kurallar)) { $kurallar += $k }
    }
    $e = $Config.etiketler
    # Hizli esleme tablosu: her kuralin 'ne_zaman' kosullari -> arac (ihtiyac ve oncelik sirasiyla)
    $satirlar.Add('## ' + $e.esleme)
    $satirlar.Add($e.esleme_aciklama)
    $satirlar.Add('')
    $satirlar.Add('| ' + $e.kosul + ' | ' + $e.arac + ' |')
    $satirlar.Add('|---|---|')
    foreach ($ih in @($Config.ihtiyaclar)) {
        foreach ($k in @($kurallar | Where-Object { $_.ihtiyac -eq $ih.id } | Sort-Object { [int]$_.oncelik })) {
            foreach ($nz in @($k.ne_zaman | Where-Object { $_ })) {
                $satirlar.Add('| ' + ($nz -replace '\|', '/') + ' | **' + $k.arac + '** |')
            }
        }
    }
    $satirlar.Add('')
    $satirlar.Add('# ' + $e.detay)
    $satirlar.Add('')
    foreach ($ih in @($Config.ihtiyaclar)) {
        $liste = @($kurallar | Where-Object { $_.ihtiyac -eq $ih.id } | Sort-Object { [int]$_.oncelik })
        if ($liste.Count -eq 0) { continue }
        $satirlar.Add('## ' + $ih.baslik)
        if ($ih.tetik) { $satirlar.Add('**' + $e.tetik + ':** ' + $ih.tetik) }
        if ($liste.Count -gt 1) { $satirlar.Add($e.sira + ' ' + (($liste | ForEach-Object { $_.arac }) -join ' > ')) }
        $satirlar.Add('')
        $i = 1
        foreach ($k in $liste) {
            $satirlar.Add(('### {0}. **{1}**' -f $i, $k.arac))
            if ($k.metin) { $satirlar.Add('- **' + $e.amac + ':** ' + $k.metin) }
            if (@($k.ne_zaman | Where-Object { $_ }).Count -gt 0) { $satirlar.Add('- **' + $e.ne_zaman + ':** ' + (@($k.ne_zaman | Where-Object { $_ }) -join '; ')) }
            if (@($k.ne_zaman_degil | Where-Object { $_ }).Count -gt 0) { $satirlar.Add('- **' + $e.ne_zaman_degil + ':** ' + (@($k.ne_zaman_degil | Where-Object { $_ }) -join '; ')) }
            if (@($k.nasil | Where-Object { $_ }).Count -gt 0) { $satirlar.Add('- **' + $e.nasil + ':** ' + (@($k.nasil | Where-Object { $_ }) -join '; ')) }
            if ($k.dogrula) { $satirlar.Add('- **' + $e.dogrula + ':** ' + $k.dogrula) }
            $satirlar.Add('')
            $i++
        }
        if ($ih.not) { $satirlar.Add('> ' + $e.not + ': ' + $ih.not); $satirlar.Add('') }
    }
    return (($satirlar -join $nl).TrimEnd() + $nl)
}

function Get-Bagimliliklarla([string[]]$Idler) {
    $secili = New-Object System.Collections.Generic.HashSet[string]
    $yigin = New-Object System.Collections.Stack
    foreach ($i in $Idler) { $yigin.Push($i) }
    while ($yigin.Count -gt 0) {
        $i = [string]$yigin.Pop()
        if (-not $IdTablo.ContainsKey($i)) { Write-Log "Bilinmeyen bilesen: $i" 'UYARI'; continue }
        if ($secili.Add($i)) { foreach ($g in @($IdTablo[$i].gerekir)) { if ($g) { $yigin.Push($g) } } }
    }
    # JSON sirasini koru (bagimliliklar listede once gelir)
    return @($Tum | Where-Object { $secili.Contains($_.id) })
}

Update-EnvPath
Write-Log "RepoKurulum $($Config.surum) - log: $LogFile"

if ($Kurallar -or $TumKurallar) {
    # Sadece metni yazdirir:  RepoKurulum.ps1 -Kurallar | Set-Clipboard
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    Get-KuralMetni -Hepsi:$TumKurallar
    exit 0
}

# ------------------------------------------------------------------ Guncelleme ve yeni bilesen tespiti
$script:Guncellemeler = @{}      # id -> aciklama (guncelleme var)
$script:YeniBilesenler = @{}     # id -> $true (kullanici ilk kez goruyor)
$script:UvListe = $null
$SurumDosyasi = Join-Path $env:LOCALAPPDATA 'RepoKurulum\surumler.json'
$GorulduDosyasi = Join-Path $env:LOCALAPPDATA 'RepoKurulum\goruldu.json'

function Read-JsonTablo([string]$Yol) {
    $t = @{}
    if (Test-Path -LiteralPath $Yol) {
        try { $j = [IO.File]::ReadAllText($Yol) | ConvertFrom-Json; foreach ($p in $j.PSObject.Properties) { $t[$p.Name] = $p.Value } } catch { }
    }
    return $t
}
function Write-JsonTablo([string]$Yol, $Tablo) {
    try { [IO.File]::WriteAllText($Yol, ($Tablo | ConvertTo-Json -Depth 4), (New-Object System.Text.UTF8Encoding($false))) } catch { }
}

function Find-YeniBilesenler {
    # Ilk calistirmada hepsi "goruldu" sayilir; sonra eklenenler "Yeni" olur
    $script:YeniBilesenler = @{}
    if (-not (Test-Path -LiteralPath $GorulduDosyasi)) { return }
    $g = Read-JsonTablo $GorulduDosyasi
    foreach ($b in $Tum) { if (-not $g.ContainsKey($b.id)) { $script:YeniBilesenler[$b.id] = $true } }
}
function Save-Goruldu {
    $g = @{}
    foreach ($b in $Tum) { $g[$b.id] = $true }
    Write-JsonTablo $GorulduDosyasi $g
}

function Get-UzakHead([string]$Url) {
    Invoke-Harici 'git' @('ls-remote', $Url, 'HEAD') -ZamanAsimi 60 -Sessizce | Out-Null
    $m = [regex]::Match([string]$script:SonCikti, '^([0-9a-f]{40})\s+HEAD', 'Multiline')
    if ($m.Success) { return $m.Groups[1].Value }
    return $null
}

function Get-UvSurum([string]$Paket) {
    if ($null -eq $script:UvListe) {
        Invoke-Harici 'uv' @('tool', 'list') -ZamanAsimi 60 -Sessizce | Out-Null
        $script:UvListe = [string]$script:SonCikti
    }
    $m = [regex]::Match($script:UvListe, '(?m)^' + [regex]::Escape($Paket) + '\s+v(\S+)')
    if ($m.Success) { return $m.Groups[1].Value }
    return $null
}

function Test-Guncelleme($B) {
    # Kurulu bir bilesen icin yeni surum var mi? Varsa kisa aciklama, yoksa $null
    if (-not (Test-DosyalarGuncel $B)) { return 'kurulum dosyalari degisti' }
    $g = $B.guncelleme
    if (-not $g) { return $null }
    try {
        switch ($g.tur) {
            'pypi' {
                $kurulu = Get-UvSurum $g.paket
                if (-not $kurulu) { return $null }
                $son = (Invoke-RestMethod -Uri ("https://pypi.org/pypi/{0}/json" -f $g.paket) -TimeoutSec 20).info.version
                if ($son -and $son -ne $kurulu) { return "$kurulu -> $son" }
            }
            'git' {
                $dizin = Expand-Deger $g.dizin
                if (-not (Test-Path -LiteralPath (Join-Path $dizin '.git'))) { return $null }
                Invoke-Harici 'git' @('-C', $dizin, 'rev-parse', 'HEAD') -ZamanAsimi 30 -Sessizce | Out-Null
                $yerel = ([string]$script:SonCikti).Trim()
                $uzak = Get-UzakHead $g.url
                if ($uzak -and $yerel -and $uzak -ne $yerel) { return 'yeni commit' }
            }
            'plugin' {
                $uzak = Get-UzakHead $g.url
                if (-not $uzak) { return $null }
                $t = Read-JsonTablo $SurumDosyasi
                if (-not $t.ContainsKey($B.id)) { $t[$B.id] = $uzak; Write-JsonTablo $SurumDosyasi $t; return $null }
                if ($t[$B.id] -ne $uzak) { return 'eklentide yeni surum' }
            }
            'claude' {
                # Kurulu surum (claude --version -> "2.1.319 (Claude Code)") ile npm'deki son surum
                Invoke-Harici 'claude' @('--version') -ZamanAsimi 60 -Sessizce | Out-Null
                $m = [regex]::Match([string]$script:SonCikti, '(\d+\.\d+\.\d+)')
                if (-not $m.Success) { return $null }
                $kurulu = $m.Groups[1].Value
                $son = (Invoke-RestMethod -Uri 'https://registry.npmjs.org/@anthropic-ai/claude-code/latest' -TimeoutSec 20).version
                if ($son -and ([version]$son -gt [version]$kurulu)) { return "$kurulu -> $son" }
            }
            'winget' {
                if (-not (Test-Komut 'winget')) { return $null }
                Invoke-Harici 'winget' @('list', '--id', $g.id, '-e', '--upgrade-available', '--accept-source-agreements', '--disable-interactivity') -ZamanAsimi 90 -Sessizce | Out-Null
                if ([string]$script:SonCikti -match [regex]::Escape($g.id)) { return 'winget guncellemesi' }
            }
        }
    } catch { Write-Log "Guncelleme kontrolu yapilamadi ($($B.id)): $($_.Exception.Message)" 'UYARI' }
    return $null
}

function Find-Guncellemeler {
    $script:Guncellemeler = @{}
    $script:UvListe = $null
    foreach ($b in $Tum) {
        if (-not (Test-BilesenTemel $b)) { continue }
        if ($script:DurumEtiketi) { $script:DurumEtiketi.Text = "  Guncellemeler kontrol ediliyor: $($b.ad)" }
        Invoke-UiPump
        $a = Test-Guncelleme $b
        if ($a) { $script:Guncellemeler[$b.id] = $a; Write-Log "Guncelleme var: $($b.ad) ($a)" 'UYARI' }
    }
    if ($script:DurumEtiketi) { $script:DurumEtiketi.Text = '  Hazir' }
}

function Invoke-Guncelleme($B) {
    # Kurulu bileseni gunceller. Kurulum dosyalari degistiyse normal kurulum adimlari tekrar calisir.
    Write-Log "==== $($B.ad): guncelleniyor ($($script:Guncellemeler[$B.id])) ===="
    if (-not (Test-DosyalarGuncel $B)) {
        foreach ($adim in @($B.kur)[0]) { $kod = Invoke-Adim $adim; if ($kod -ne 0) { return 'Hata' } }
        return 'Guncellendi'
    }
    $g = $B.guncelleme
    $kod = 1
    switch ($g.tur) {
        'pypi' { $kod = Invoke-Harici 'uv' @('tool', 'upgrade', $g.paket) }
        'git' {
            $dizin = Expand-Deger $g.dizin
            $kod = Invoke-Harici 'git' @('-C', $dizin, 'fetch', '--depth', '1', 'origin', 'HEAD')
            if ($kod -eq 0) {
                $kod = Invoke-Harici 'git' @('-C', $dizin, 'merge', '--ff-only', 'FETCH_HEAD')
                if ($kod -ne 0) { Write-Log "Klasorde senin degisikliklerin var, otomatik guncellenmedi: $dizin (git -C ... pull ile elle guncelle)" 'UYARI' }
            }
        }
        'plugin' {
            Invoke-Harici 'claude' @('plugin', 'marketplace', 'update', $g.marketplace) | Out-Null
            $kod = Invoke-Harici 'claude' @('plugin', 'update', $g.eklenti)
            if ($kod -eq 0) { $t = Read-JsonTablo $SurumDosyasi; $t[$B.id] = (Get-UzakHead $g.url); Write-JsonTablo $SurumDosyasi $t }
        }
        'claude' {
            # Claude Code'un kendi guncelleyicisi; acik oturumlar bir sonraki acilista yeni surume gecer
            $kod = Invoke-Harici 'claude' @('update') -ZamanAsimi 600
            if ($kod -eq 0) { Write-Log "Claude Code guncellendi. Acik Claude pencerelerini kapatip yeniden acinca yeni surum calisir." 'OK' }
        }
        'winget' {
            $kod = Invoke-Harici 'winget' @('upgrade', '--id', $g.id, '-e', '--silent', '--accept-package-agreements', '--accept-source-agreements', '--disable-interactivity')
            if ($kod -in @(-1978335189, -1978335135)) { $kod = 0 }
            if ($kod -ne 0) {
                # Sistem araci guncellemesi istege bagli: hata sayma, nedenini ve cozumunu yaz
                $son = (([string]$script:SonCikti -split "`n") | Where-Object { $_.Trim() } | Select-Object -Last 3) -join ' / '
                Write-Log ("{0} guncellenemedi (winget cikis kodu 0x{1:X8}): {2}" -f $B.ad, $kod, $son) 'UYARI'
                Write-Log ("Cozum: Claude Code ve Git Bash/terminal pencerelerini kapat, YONETICI PowerShell'de calistir:  winget upgrade --id {0} -e" -f $g.id) 'UYARI'
                return 'Atlandi'
            }
        }
    }
    Update-EnvPath; Reset-Onbellek
    if ($kod -eq 0) { $script:Guncellemeler.Remove($B.id); Write-Log "$($B.ad) guncellendi" 'OK'; return 'Guncellendi' }
    $script:Hatalar++
    Write-Log "$($B.ad) guncellenemedi. Ayrinti: $LogFile" 'HATA'
    return 'Hata'
}

if ($GuncellemeKontrol -or $Guncelle) {
    Find-Guncellemeler
    if ($script:Guncellemeler.Count -eq 0) { Write-Log 'Guncelleme yok' 'OK' }
    foreach ($k in @($script:Guncellemeler.Keys)) { '{0,-22} {1}' -f $k, $script:Guncellemeler[$k] }
    if ($Guncelle) { foreach ($b in $Tum) { if ($script:Guncellemeler.ContainsKey($b.id)) { Invoke-Guncelleme $b | Out-Null } } }
    exit $script:Hatalar
}

if ($Liste) {
    foreach ($b in $Tum) {
        $durum = 'yok'
        if (Test-Bilesen $b) { $durum = 'KURULU' }
        '{0,-22} {1,-8} {2,-12} {3}' -f $b.id, $durum, $b.lisans, $b.ad
    }
    exit 0
}

if ($Sessiz) {
    if ($Bilesenler) { $idler = $Bilesenler.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ } }
    else { $idler = @($Tum | Where-Object { $_.varsayilan } | ForEach-Object { $_.id }) }
    $plan = Get-Bagimliliklarla $idler
    Write-Log ("Kurulacak: " + (($plan | ForEach-Object { $_.id }) -join ', '))
    $ozet = @()
    foreach ($b in $plan) { $ozet += ('{0,-22} {1}' -f $b.id, (Install-Bilesen $b)) }
    Write-Log '---------------- OZET ----------------'
    foreach ($s in $ozet) { Write-Log $s }
    Write-Log "Hata sayisi: $($script:Hatalar)" $(if ($script:Hatalar) { 'HATA' } else { 'OK' })
    exit $script:Hatalar
}

# ------------------------------------------------------------------ Arayuz
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

# Pencere gizli konsoldan acildigi icin beklenmeyen hatalar kullaniciya kutuyla gosterilir
trap {
    $m = "Beklenmeyen hata: $($_.Exception.Message)`r`n`r`nLog: $LogFile"
    try { Add-Content -LiteralPath $LogFile -Value $m -Encoding UTF8 } catch { }
    if ($script:LogBox) { [System.Windows.Forms.MessageBox]::Show($m, 'Repo Kurulum') | Out-Null }
    else { Write-Host $m -ForegroundColor Red }
    continue
}

$form = New-Object System.Windows.Forms.Form
$form.Text = "Repo Kurulum $($Config.surum) - Claude Code / MCP / Skill"
$form.Size = New-Object System.Drawing.Size(1000, 720)
$form.MinimumSize = New-Object System.Drawing.Size(820, 560)
$form.StartPosition = 'CenterScreen'
$form.Font = New-Object System.Drawing.Font('Segoe UI', 9)

$ust = New-Object System.Windows.Forms.Label
$ust.Text = "Kurmak istediklerini isaretle ve 'Secilenleri Kur'a bas. Kurulu olanlar atlanir; bagimliliklar otomatik secilir. Anahtar isteyenler icin pencere acilir."
$ust.Dock = 'Top'; $ust.Height = 34; $ust.Padding = New-Object System.Windows.Forms.Padding(8, 8, 8, 0)

$bant = New-Object System.Windows.Forms.Label
$bant.Dock = 'Top'; $bant.Height = 30; $bant.TextAlign = 'MiddleLeft'; $bant.Visible = $false
$bant.BackColor = [System.Drawing.Color]::FromArgb(255, 236, 153)
$bant.ForeColor = [System.Drawing.Color]::FromArgb(90, 60, 0)
$bant.Font = New-Object System.Drawing.Font('Segoe UI', 9, [System.Drawing.FontStyle]::Bold)
$script:Bant = $bant

$lv = New-Object System.Windows.Forms.ListView
$lv.View = 'Details'; $lv.CheckBoxes = $true; $lv.FullRowSelect = $true; $lv.GridLines = $true
$lv.Dock = 'Fill'; $lv.ShowItemToolTips = $true
[void]$lv.Columns.Add('Bilesen', 230)
[void]$lv.Columns.Add('Durum', 105)
[void]$lv.Columns.Add('Lisans', 110)
[void]$lv.Columns.Add('Ne ise yarar', 520)
$script:ListView = $lv

$gruplar = @{}
$script:AsilGrup = @{}
$script:GrupUst = New-Object System.Windows.Forms.ListViewGroup('0. Guncelleme / Yeni', '0. Guncelleme / Yeni')
[void]$lv.Groups.Add($script:GrupUst)
foreach ($b in $Tum) {
    if (-not $gruplar.ContainsKey($b.kategori)) {
        $g = New-Object System.Windows.Forms.ListViewGroup($b.kategori, $b.kategori)
        [void]$lv.Groups.Add($g); $gruplar[$b.kategori] = $g
    }
    $it = New-Object System.Windows.Forms.ListViewItem($b.ad)
    [void]$it.SubItems.Add('...')
    [void]$it.SubItems.Add([string]$b.lisans)
    [void]$it.SubItems.Add([string]$b.aciklama)
    $it.Group = $gruplar[$b.kategori]
    $script:AsilGrup[$b.id] = $gruplar[$b.kategori]
    $it.Tag = $b.id
    $it.ToolTipText = [string]$b.repo
    $it.Checked = [bool]$b.varsayilan
    [void]$lv.Items.Add($it)
}

$script:BagimlilikKilit = $false
$lv.add_ItemChecked({
    param($s, $e)
    if ($script:BagimlilikKilit -or -not $e.Item.Checked) { return }
    $script:BagimlilikKilit = $true
    try {
        $gerekli = Get-Bagimliliklarla @([string]$e.Item.Tag)
        foreach ($it in $script:ListView.Items) {
            if ($gerekli | Where-Object { $_.id -eq $it.Tag }) { $it.Checked = $true }
        }
    } finally { $script:BagimlilikKilit = $false }
})
$lv.add_ItemActivate({
    $sec = $script:ListView.SelectedItems
    if ($sec.Count -gt 0 -and $sec[0].ToolTipText) { Start-Process $sec[0].ToolTipText }
})

function Set-Durum([string]$Id, [string]$Durum) {
    foreach ($it in $script:ListView.Items) {
        if ($it.Tag -eq $Id) {
            $it.SubItems[1].Text = $Durum
            switch ($Durum) {
                'Kurulu'  { $it.ForeColor = [System.Drawing.Color]::DarkGreen }
                'Kuruldu' { $it.ForeColor = [System.Drawing.Color]::Green }
                'Hata'    { $it.ForeColor = [System.Drawing.Color]::Red }
                'Atlandi' { $it.ForeColor = [System.Drawing.Color]::DarkOrange }
                'Guncelleme var' { $it.ForeColor = [System.Drawing.Color]::Blue }
                'Guncellendi' { $it.ForeColor = [System.Drawing.Color]::Green }
                'Yeni'    { $it.ForeColor = [System.Drawing.Color]::Purple }
                default   { $it.ForeColor = [System.Drawing.SystemColors]::WindowText }
            }
        }
    }
    Invoke-UiPump
}

function Update-TumDurumlar {
    Reset-Onbellek
    Update-EnvPath
    foreach ($b in $Tum) {
        $d = 'Yok'
        if (Test-BilesenTemel $b) {
            $d = 'Kurulu'
            # Hizli kontrol: kurulum dosyalari degistiyse hemen goster (ag gerektirmez)
            if (-not (Test-DosyalarGuncel $b)) { $script:Guncellemeler[$b.id] = 'kurulum dosyalari degisti' }
            if ($script:Guncellemeler.ContainsKey($b.id)) { $d = 'Guncelleme var' }
        } elseif ($script:YeniBilesenler.ContainsKey($b.id)) { $d = 'Yeni' }
        Set-Durum $b.id $d
        # Uygulama/skill guncellemeleri otomatik isaretlenir; sistem araclari (winget) istege bagli
        if ($d -eq 'Guncelleme var' -and -not ($b.guncelleme.tur -eq 'winget' -and $script:Guncellemeler[$b.id] -eq 'winget guncellemesi')) {
            foreach ($it in $script:ListView.Items) { if ($it.Tag -eq $b.id) { $it.Checked = $true } }
        }
    }
    Update-UstGrup
}

function Update-UstGrup {
    # Guncellemesi olan ve yeni bilesenleri listenin en ustundeki gruba tasi, bilgi seridini guncelle
    $gun = @(); $yen = @()
    foreach ($it in $script:ListView.Items) {
        $id = [string]$it.Tag
        $ustte = $false
        if ($script:Guncellemeler.ContainsKey($id) -and $it.SubItems[1].Text -eq 'Guncelleme var') { $ustte = $true; $gun += $it.Text }
        elseif ($it.SubItems[1].Text -eq 'Yeni') { $ustte = $true; $yen += $it.Text }
        if ($ustte) { $it.Group = $script:GrupUst } else { $it.Group = $script:AsilGrup[$id] }
    }
    $parcalar = @()
    if ($gun.Count -gt 0) { $parcalar += ('GUNCELLEME VAR ({0}): {1}  -> isaretliler Secilenleri Kur ile guncellenir (sistem araclari istege bagli)' -f $gun.Count, ($gun -join ', ')) }
    if ($yen.Count -gt 0) { $parcalar += ('YENI BILESEN ({0}): {1}' -f $yen.Count, ($yen -join ', ')) }
    if ($parcalar.Count -gt 0) { $script:Bant.Text = '  ' + ($parcalar -join '     |     '); $script:Bant.Visible = $true }
    else { $script:Bant.Visible = $false }
}

$log = New-Object System.Windows.Forms.TextBox
$log.Multiline = $true; $log.ScrollBars = 'Vertical'; $log.ReadOnly = $true
$log.Dock = 'Bottom'; $log.Height = 200
$log.Font = New-Object System.Drawing.Font('Consolas', 9)
$log.BackColor = [System.Drawing.Color]::FromArgb(30, 30, 30)
$log.ForeColor = [System.Drawing.Color]::Gainsboro

$progress = New-Object System.Windows.Forms.ProgressBar
$progress.Dock = 'Bottom'; $progress.Height = 14

$durum = New-Object System.Windows.Forms.Label
$durum.Dock = 'Bottom'; $durum.Height = 22; $durum.TextAlign = 'MiddleLeft'
$durum.Font = New-Object System.Drawing.Font('Consolas', 9, [System.Drawing.FontStyle]::Bold)
$durum.Text = '  Hazir'

$panel = New-Object System.Windows.Forms.FlowLayoutPanel
$panel.Dock = 'Bottom'; $panel.Height = 84; $panel.Padding = New-Object System.Windows.Forms.Padding(6)

function New-Dugme([string]$Metin, [int]$Genislik = 140) {
    $d = New-Object System.Windows.Forms.Button
    $d.Text = $Metin; $d.Width = $Genislik; $d.Height = 30
    [void]$panel.Controls.Add($d)
    return $d
}

$btnKur      = New-Dugme 'Secilenleri Kur' 150
$btnKur.Font = New-Object System.Drawing.Font('Segoe UI', 9, [System.Drawing.FontStyle]::Bold)
$btnYenile   = New-Dugme 'Durumu Yenile'
$btnGuncel   = New-Dugme 'Guncellemeleri Kontrol Et' 170
$btnVars     = New-Dugme 'Varsayilanlari Sec'
$btnHic      = New-Dugme 'Secimi Temizle' 110
$btnClaude   = New-Dugme "Claude'u Ac (klasor sec)" 170
$btnLog      = New-Dugme 'Log Klasoru' 100
$btnKural    = New-Dugme 'Kurallari Kopyala' 140
$chkZorla    = New-Object System.Windows.Forms.CheckBox
$chkZorla.Text = 'MCP kayitlarini yeniden ekle'; $chkZorla.Width = 200; $chkZorla.Height = 30
[void]$panel.Controls.Add($chkZorla)

$btnVars.add_Click({ foreach ($it in $script:ListView.Items) { $it.Checked = [bool]$IdTablo[[string]$it.Tag].varsayilan } })
$btnHic.add_Click({ foreach ($it in $script:ListView.Items) { $it.Checked = $false } })
$btnLog.add_Click({ Start-Process explorer.exe $LogDir })
$btnKural.add_Click({
    $form.UseWaitCursor = $true
    Reset-Onbellek
    $metin = Get-KuralMetni
    $form.UseWaitCursor = $false
    [System.Windows.Forms.Clipboard]::SetText($metin.Replace("`n", "`r`n"))
    $yol = Join-Path $env:USERPROFILE '.claude\CLAUDE.md'
    Write-Log 'Arac secim kurallari panoya kopyalandi (sadece kurulu araclar). Hicbir dosya degistirilmedi.' 'OK'
    [System.Windows.Forms.MessageBox]::Show("Kurulu araclarin secim kurallari panoya kopyalandi.`r`n`r`nSimdi su dosyayi ac ve Ctrl+V ile yapistir:`r`n$yol`r`n`r`nDosyada eski bir 'Arac secim kurallari' bolumu varsa once onu sil (iki kez olmasin).", 'Kurallar kopyalandi') | Out-Null
})
$btnYenile.add_Click({ $form.UseWaitCursor = $true; Update-TumDurumlar; $form.UseWaitCursor = $false })
$btnGuncel.add_Click({
    foreach ($c in $panel.Controls) { $c.Enabled = $false }
    Find-Guncellemeler
    Update-TumDurumlar
    foreach ($c in $panel.Controls) { $c.Enabled = $true }
    if ($script:Guncellemeler.Count -eq 0) { Write-Log 'Kurulu bilesenler guncel.' 'OK' }
})
$btnClaude.add_Click({
    Update-EnvPath
    if (-not (Test-Komut 'claude')) { [System.Windows.Forms.MessageBox]::Show('Claude Code henuz kurulu degil.') | Out-Null; return }
    # Klasoru kullanici secsin: ClaudeAc.bat (son klasor / klasor sec / yeni-devam-eski konusma)
    $bat = Join-Path $script:Kok 'ClaudeAc.bat'
    if (Test-Path -LiteralPath $bat) {
        Start-Process $env:ComSpec -ArgumentList '/c', ('"' + $bat + '"') -WorkingDirectory $env:USERPROFILE
    } else {
        Start-Process $env:ComSpec -ArgumentList '/k', 'claude' -WorkingDirectory $env:USERPROFILE
    }
})

$btnKur.add_Click({
    $idler = @($script:ListView.CheckedItems | ForEach-Object { [string]$_.Tag })
    if ($idler.Count -eq 0) { [System.Windows.Forms.MessageBox]::Show('Hicbir bilesen secilmedi.') | Out-Null; return }
    $script:Zorla = $chkZorla.Checked
    Set-Variable -Name Zorla -Value $chkZorla.Checked -Scope Script
    foreach ($c in $panel.Controls) { $c.Enabled = $false }
    $script:ListView.Enabled = $false
    $script:Hatalar = 0
    $plan = Get-Bagimliliklarla $idler
    $progress.Maximum = [Math]::Max(1, $plan.Count); $progress.Value = 0
    try {
        foreach ($b in $plan) {
            Set-Durum $b.id 'Kuruluyor'
            $sonuc = Install-Bilesen $b
            Set-Durum $b.id $sonuc
            $progress.Value = [Math]::Min($progress.Maximum, $progress.Value + 1)
        }
    } catch {
        Write-Log "Beklenmeyen hata: $($_.Exception.Message)" 'HATA'
        $script:Hatalar++
    } finally {
        foreach ($c in $panel.Controls) { $c.Enabled = $true }
        $script:ListView.Enabled = $true
        Update-UstGrup
    }
    if ($script:Hatalar -eq 0) {
        Write-Log "TAMAMLANDI. Simdi 'Claude'u Ac (klasor sec)' ile klasorunu sec, giris yap ve /mcp yaz." 'OK'
        [System.Windows.Forms.MessageBox]::Show("Kurulum tamamlandi.`r`n`r`nSonraki adim: 'Claude'u Ac (klasor sec)' dugmesine bas, calisacagin klasoru sec; ilk acilista tarayicida giris yap, sonra /mcp yaz.", 'Repo Kurulum') | Out-Null
    } else {
        Write-Log "$($script:Hatalar) bilesen kurulamadi. Log: $LogFile" 'HATA'
        [System.Windows.Forms.MessageBox]::Show("$($script:Hatalar) bilesen kurulamadi.`r`nLog: $LogFile`r`n`r`nInternet/proxy'yi kontrol edip tekrar 'Secilenleri Kur'a basabilirsin.", 'Repo Kurulum') | Out-Null
    }
})

# Dock sirasi: once Fill, sonra Bottom/Top (WinForms ters sirayla yerlestirir)
$form.Controls.Add($lv)
$form.Controls.Add($panel)
$form.Controls.Add($durum)
$form.Controls.Add($progress)
$form.Controls.Add($log)
$form.Controls.Add($bant)
$form.Controls.Add($ust)
$script:LogBox = $log
$script:DurumEtiketi = $durum

$form.TopMost = $true   # baska pencerelerin arkasinda acilmasin
$form.add_Shown({
    $form.Activate()
    $form.TopMost = $false
    Write-Log "Log dosyasi: $LogFile"
    if (-not (Test-Komut 'winget')) { Write-Log "winget bulunamadi. Microsoft Store'dan 'App Installer' kur; bazi bilesenler alternatif yontemle kurulur." 'UYARI' }
    $form.UseWaitCursor = $true
    Find-YeniBilesenler
    Update-TumDurumlar
    $form.UseWaitCursor = $false
    if ($env:REPOKURULUM_ARAYUZ_TEST -ne '1') {
        # Ag kontrolu pencere acildiktan sonra; bu sirada dugmeler kapali
        foreach ($c in $panel.Controls) { $c.Enabled = $false }
        Find-Guncellemeler
        Update-TumDurumlar
        foreach ($c in $panel.Controls) { $c.Enabled = $true }
    }
    if ($env:REPOKURULUM_ARAYUZ_TEST -eq '1') {
        Write-Log ("ARAYUZ_OK - {0} satir listelendi" -f $script:ListView.Items.Count) 'OK'
        $form.Close()
    }
})

$form.add_FormClosing({ Save-Goruldu })
[void]$form.ShowDialog()
