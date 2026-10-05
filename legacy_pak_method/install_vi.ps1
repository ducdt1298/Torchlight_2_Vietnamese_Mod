<#
  Torchlight II - install the Vietnamese language pack into DATA.PAK (method B, abandoned).

  - Only APPENDS the language pack to the end of DATA.PAK and replaces DATA.PAK.MAN with a version
    that also registers the new files. The original game data stays byte-for-byte identical.
  - Backs up the original DATA.PAK.MAN as PAKS\DATA.PAK.MAN.vi-backup.
  - If another build of the Vietnamese pack is installed, uninstalls it first.
  - Uninstall: run uninstall_vi.bat.

  Parameters:
    -GameDir "<path>"        Torchlight II install folder (default: looked up in the registry)
    -SkipHashCheck           skip the SHA-256 check of the whole DATA.PAK (faster)
#>
param(
    [string]$GameDir = '',
    [switch]$SkipHashCheck
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
. (Join-Path $root 'tools\vi_common.ps1')

$ctx = Get-Context $root $GameDir
$info = $ctx.Info
$append = Join-Path $root 'output\PAKS\DATA.PAK.vi-append'
$newMan = Join-Path $root 'output\PAKS\DATA.PAK.MAN'
Write-Host "Thu muc game: $($ctx.GameDir)"
Assert-NotRunning

if ((Sha $append) -ne $info.append.sha256) { Fail 'File output\PAKS\DATA.PAK.vi-append bi hong hoac khong dung ban.' }
if ((Sha $newMan) -ne $info.patched.man_sha256) { Fail 'File output\PAKS\DATA.PAK.MAN bi hong hoac khong dung ban.' }

$state = Get-PakState $ctx
if ($state -eq 'installed') { Write-Host 'Goi Viet hoa (phien ban nay) da duoc cai tu truoc.' -ForegroundColor Yellow; exit 0 }
if ($state -eq 'other-version') {
    Write-Host 'Phat hien mot phien ban khac cua goi Viet hoa - go no truoc...'
    Restore-Original $ctx -SkipHashCheck:$SkipHashCheck
    $state = Get-PakState $ctx
}
if ($state -ne 'original') {
    Fail 'DATA.PAK / DATA.PAK.MAN khong khop voi ban game dung de build (game da cap nhat hoac da bi sua). Hay build lai: python tools\build_all.py'
}
if (-not $SkipHashCheck) {
    Write-Host 'Dang kiem tra DATA.PAK (SHA-256, mat vai giay)...'
    if ((Sha $ctx.Pak) -ne $info.original.pak_sha256) { Fail 'Noi dung DATA.PAK khong khop ban da build. Hay build lai.' }
}

Copy-Item -Path $ctx.Man -Destination $ctx.Backup -Force
$bytes = [System.IO.File]::ReadAllBytes($append)
$fs = [System.IO.File]::Open($ctx.Pak, [System.IO.FileMode]::Append, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
try { $fs.Write($bytes, 0, $bytes.Length); $fs.Flush() } finally { $fs.Close() }
Copy-Item -Path $newMan -Destination $ctx.Man -Force

if ((Get-PakState $ctx) -ne 'installed') {
    Set-PakLength $ctx.Pak $ctx.OrigSize
    Copy-Item -Path $ctx.Backup -Destination $ctx.Man -Force
    Fail 'Kiem tra sau khi cai that bai - da hoan tac ve trang thai goc.'
}
Write-Host ''
Write-Host 'Cai dat thanh cong!' -ForegroundColor Green
Write-Host 'Vao game: Options > Language > chon "Tieng Viet", roi khoi dong lai game.'
