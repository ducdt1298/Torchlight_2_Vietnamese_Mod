# Shared helpers for legacy_pak_method/install_vi.ps1 / uninstall_vi.ps1 (dot-sourced).
# ASCII only (Windows PowerShell 5.1); user messages are Vietnamese without diacritics.

function Fail([string]$msg) { Write-Host "LOI: $msg" -ForegroundColor Red; exit 1 }

function Sha([string]$p) { (Get-FileHash -Algorithm SHA256 -Path $p).Hash.ToLower() }

function Sha-Prefix([string]$path, [int64]$length) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $fs = [System.IO.File]::OpenRead($path)
    try {
        $buf = New-Object byte[] 16777216
        $left = $length
        while ($left -gt 0) {
            $want = [int][Math]::Min([int64]$buf.Length, $left)
            $n = $fs.Read($buf, 0, $want)
            if ($n -le 0) { break }
            [void]$sha.TransformBlock($buf, 0, $n, $null, 0)
            $left -= $n
        }
        [void]$sha.TransformFinalBlock($buf, 0, 0)
        return ([BitConverter]::ToString($sha.Hash) -replace '-', '').ToLower()
    } finally { $fs.Close(); $sha.Dispose() }
}

function Find-GameDir {
    foreach ($key in 'HKLM:\SOFTWARE\WOW6432Node\Runic Games\Torchlight II', 'HKLM:\SOFTWARE\Runic Games\Torchlight II') {
        try {
            $d = (Get-ItemProperty -Path $key -Name instdir -ErrorAction Stop).instdir
            if ($d -and (Test-Path (Join-Path $d 'PAKS\DATA.PAK'))) { return $d }
        } catch { }
    }
    return 'D:\SteamLibrary\steamapps\common\Torchlight II'
}

function Get-Context([string]$root, [string]$gameDir) {
    if (-not $gameDir) { $gameDir = Find-GameDir }
    $infoPath = Join-Path $root 'output\patch_info.json'
    if (-not (Test-Path $infoPath)) { Fail "Khong tim thay $infoPath - hay build truoc: python tools\build_all.py" }
    $info = Get-Content -Raw -Encoding UTF8 -Path $infoPath | ConvertFrom-Json
    $pak = Join-Path $gameDir 'PAKS\DATA.PAK'
    $man = Join-Path $gameDir 'PAKS\DATA.PAK.MAN'
    if (-not (Test-Path $pak) -or -not (Test-Path $man)) { Fail "Khong tim thay $pak" }
    return [pscustomobject]@{
        Root = $root; GameDir = $gameDir; Info = $info; Pak = $pak; Man = $man
        Backup = "$man.vi-backup"
        OrigSize = [int64]$info.original.pak_size; PatchedSize = [int64]$info.patched.pak_size
        OrigManCopy = Join-Path $root 'output\PAKS\DATA.PAK.MAN.original'
    }
}

function Assert-NotRunning {
    if (Get-Process -Name 'Torchlight2', 'ModLauncher' -ErrorAction SilentlyContinue) {
        Fail 'Hay thoat Torchlight II (va ModLauncher) truoc.'
    }
}

# original       : DATA.PAK and MAN are exactly the version the patch was built from
# installed      : exactly this build of the Vietnamese pack is installed
# other-version  : DATA.PAK is longer than the original and a saved original MAN exists
#                  (another build of this pack); verified again before any change
# unknown        : anything else (game updated, other modifications)
function Get-PakState($ctx) {
    $size = (Get-Item $ctx.Pak).Length
    $manSha = Sha $ctx.Man
    if ($size -eq $ctx.OrigSize -and $manSha -eq $ctx.Info.original.man_sha256) { return 'original' }
    if ($size -eq $ctx.PatchedSize -and $manSha -eq $ctx.Info.patched.man_sha256) { return 'installed' }
    if ($size -gt $ctx.OrigSize -and (Get-OriginalManSource $ctx)) { return 'other-version' }
    return 'unknown'
}

function Get-OriginalManSource($ctx) {
    foreach ($p in $ctx.Backup, $ctx.OrigManCopy) {
        if ((Test-Path $p) -and ((Sha $p) -eq $ctx.Info.original.man_sha256)) { return $p }
    }
    return $null
}

function Set-PakLength([string]$pak, [int64]$length) {
    $fs = [System.IO.File]::Open($pak, [System.IO.FileMode]::Open, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
    try { $fs.SetLength($length) } finally { $fs.Close() }
}

function Restore-Original($ctx, [switch]$SkipHashCheck) {
    $src = Get-OriginalManSource $ctx
    if (-not $src) { Fail 'Khong tim thay ban sao hop le cua DATA.PAK.MAN goc. Dung Steam > Verify integrity of game files.' }
    if (-not $SkipHashCheck) {
        Write-Host 'Dang kiem tra phan du lieu goc cua DATA.PAK (SHA-256)...'
        if ((Sha-Prefix $ctx.Pak $ctx.OrigSize) -ne $ctx.Info.original.pak_sha256) {
            Fail 'Phan du lieu goc cua DATA.PAK khong khop - khong tu go. Dung Steam > Verify integrity of game files.'
        }
    }
    Set-PakLength $ctx.Pak $ctx.OrigSize
    Copy-Item -Path $src -Destination $ctx.Man -Force
    if ((Get-PakState $ctx) -ne 'original') { Fail 'Khoi phuc that bai. Dung Steam > Verify integrity of game files.' }
}

function Reset-LanguageSetting {
    $base = $env:TL2VI_SETTINGS_BASE          # test hook; normally the user's Documents folder
    if (-not $base) { $base = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'My Games\Runic Games\Torchlight 2' }
    foreach ($sub in 'save', 'modsave') {
        $dir = Join-Path $base $sub
        if (-not (Test-Path $dir)) { continue }
        Get-ChildItem -Path $dir -Filter 'settings.txt' -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
            $p = $_.FullName
            $text = [System.IO.File]::ReadAllText($p, [System.Text.Encoding]::Unicode)
            # no "$" anchor: lines end with CRLF and .NET's multiline "$" does not match before "\r"
            $new = [regex]::Replace($text, '(?im)^LANGUAGE[ \t]*:[^\r\n]*(?:viet|vi\u1EC7t)[^\r\n]*', 'LANGUAGE :English')
            if ($new -ne $text) {
                Copy-Item -Path $p -Destination "$p.vi-backup" -Force
                [System.IO.File]::WriteAllText($p, $new, [System.Text.Encoding]::Unicode)
                Write-Host "Da dat lai ngon ngu English trong: $p"
            }
        }
    }
}
