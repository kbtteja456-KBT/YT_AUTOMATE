# PowerShell script to register YouTube Shorts Autopilot in Windows Task Scheduler
$TaskName = "YouTubeShortsAutopilot"
$VbsPath = "C:\Users\DELL\OneDrive\Desktop\yt\run_autopilot_background.vbs"

Write-Host "Registering Windows Scheduled Task '$TaskName'..." -ForegroundColor Cyan

# Action: launch wscript.exe with the background VBS script
$Action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$VbsPath`""

# Trigger: at logon of current user
$Trigger = New-ScheduledTaskTrigger -AtLogOn

# Settings: run whether plugged in or battery, restart on failure
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Days 365) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

# Register task
try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "AI YouTube Shorts Autopilot 24/7 background service for 07:00 and 18:00 IST daily publishing" -Force
    Write-Host "Task '$TaskName' successfully registered! It will run automatically when you log into Windows." -ForegroundColor Green
} catch {
    Write-Host "Error registering task: $_" -ForegroundColor Red
}
