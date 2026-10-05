<#
  Torchlight II - uninstall the Vietnamese translation mod: deletes VIETHOA_ENVI.MOD from the mods folder
  and restores modlauncher.sch.
#>
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
if (Get-Process -Name 'Torchlight2', 'ModLauncher' -ErrorAction SilentlyContinue) { Write-Host 'LOI: Hay thoat Torchlight II va ModLauncher truoc.' -ForegroundColor Red; exit 1 }
$info = Get-Content -Raw -Encoding UTF8 (Join-Path $root 'output\mod\mod_info.json') | ConvertFrom-Json
$tl = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'My Games\Runic Games\Torchlight 2'
Remove-Item (Join-Path $tl ('mods\' + $info.file)) -ErrorAction SilentlyContinue
$sch = Join-Path $tl 'modlauncher.sch'
if (Test-Path "$sch.vi-backup") { Move-Item "$sch.vi-backup" $sch -Force }
Write-Host 'Da go mod Viet hoa.' -ForegroundColor Green
