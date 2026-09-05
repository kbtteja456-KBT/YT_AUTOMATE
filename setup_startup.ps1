$startupFolder = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startupFolder 'YouTubeShortsAutopilot.lnk'
$targetVbs = 'C:\Users\DELL\OneDrive\Desktop\yt\run_autopilot_background.vbs'

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = 'wscript.exe'
$shortcut.Arguments = "`"$targetVbs`""
$shortcut.WorkingDirectory = 'C:\Users\DELL\OneDrive\Desktop\yt'
$shortcut.Description = 'AI YouTube Shorts Autopilot 24/7 Background Service'
$shortcut.Save()

Write-Host "Created startup shortcut at: $shortcutPath" -ForegroundColor Green
