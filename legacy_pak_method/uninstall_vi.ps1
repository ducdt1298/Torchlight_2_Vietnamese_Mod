<#
  Torchlight II - remove the Vietnamese language pack from DATA.PAK (any build of this pack).

  - Truncates DATA.PAK back to its original size (installing never modifies the original data),
    after checking the SHA-256 of the original data.
  - Restores the original DATA.PAK.MAN (from PAKS\DATA.PAK.MAN.vi-backup or output\PAKS\DATA.PAK.MAN.original).
  - Resets the language to English in settings.txt if Vietnamese is selected
    (so the game does not look for a language that no longer exists). Use -KeepLanguageSetting to skip this.

  Parameters:
    -GameDir "<path>"        Torchlight II install folder (default: looked up in the registry)
    -SkipHashCheck           skip the SHA-256 check of the original data
#>
param(
    [string]$GameDir = '',
    [switch]$SkipHashCheck,
    [switch]$KeepLanguageSetting
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
. (Join-Path $root 'tools\vi_common.ps1')

$ctx = Get-Context $root $GameDir
Write-Host "Thu muc game: $($ctx.GameDir)"
Assert-NotRunning

$state = Get-PakState $ctx
if ($state -eq 'original') {
    Write-Host 'Goi Viet hoa chua duoc cai (DATA.PAK dang la ban goc).' -ForegroundColor Yellow
} elseif ($state -eq 'installed' -or $state -eq 'other-version') {
    Restore-Original $ctx -SkipHashCheck:$SkipHashCheck
    Remove-Item -Path $ctx.Backup -ErrorAction SilentlyContinue
    Write-Host 'Da go goi Viet hoa. DATA.PAK va DATA.PAK.MAN da tro ve ban goc.' -ForegroundColor Green
} else {
    Fail 'DATA.PAK khong o trang thai co the tu go. De khoi phuc: Steam > Torchlight II > Properties > Installed Files > Verify integrity of game files.'
}
if (-not $KeepLanguageSetting) { Reset-LanguageSetting }
