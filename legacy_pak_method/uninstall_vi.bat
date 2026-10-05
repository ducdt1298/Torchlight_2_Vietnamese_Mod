@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall_vi.ps1" %*
pause
