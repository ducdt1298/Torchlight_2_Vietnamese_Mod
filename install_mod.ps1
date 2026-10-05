<#
  Torchlight II - install the Vietnamese translation mod (VIETHOA_ENVI.MOD).
  - Copies output\mod\VIETHOA_ENVI.MOD to Documents\My Games\Runic Games\Torchlight 2\mods\
  - Selects this mod in ModLauncher (modlauncher.sch, backed up as .vi-backup)
  - Does not touch any game file (DATA.PAK stays unchanged)
  Uninstall: uninstall_mod.bat
  Messages are Vietnamese without diacritics (ASCII only for Windows PowerShell 5.1).
#>
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
function Fail([string]$msg) { Write-Host "LOI: $msg" -ForegroundColor Red; exit 1 }
if (Get-Process -Name 'Torchlight2', 'ModLauncher' -ErrorAction SilentlyContinue) { Fail 'Hay thoat Torchlight II va ModLauncher truoc.' }

$info = Get-Content -Raw -Encoding UTF8 (Join-Path $root 'output\mod\mod_info.json') | ConvertFrom-Json
$src = Join-Path $root ('output\mod\' + $info.file)
if ((Get-FileHash $src -Algorithm SHA256).Hash.ToLower() -ne $info.sha256) { Fail "File mod bi hong: $src" }
$tl = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'My Games\Runic Games\Torchlight 2'
$mods = Join-Path $tl 'mods'
New-Item -ItemType Directory -Force $mods | Out-Null
Copy-Item $src (Join-Path $mods $info.file) -Force

$sch = Join-Path $tl 'modlauncher.sch'
if (Test-Path $sch) {
    if (-not (Test-Path "$sch.vi-backup")) { Copy-Item $sch "$sch.vi-backup" }
}
$text = "[MODS]`r`n`t<INTEGER64>MODGUID:$($info.guid)`r`n[/MODS]`r`n"
[IO.File]::WriteAllText($sch, $text, [Text.Encoding]::Unicode)
Write-Host 'Da cai mod Viet hoa.' -ForegroundColor Green
Write-Host 'Mo game > bam "Play with mods" (nut duoi) > Options > Language > Tieng Viet > khoi dong lai game (lai bam "Play with mods").'
