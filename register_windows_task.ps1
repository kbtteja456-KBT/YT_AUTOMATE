# PowerShell script to register 100% autonomous YouTube Shorts publishing in Windows Task Scheduler
# Targets: 07:00 AM IST (Slot 1) and 18:00 PM IST (Slot 2) daily

$baseDir = "C:\Users\DELL\OneDrive\Desktop\yt"
$vbsMorning = Join-Path $baseDir "run_morning_slot_silent.vbs"
$vbsEvening = Join-Path $baseDir "run_evening_slot_silent.vbs"

Write-Host "Registering Autonomous YouTube Shorts Tasks in Windows Task Scheduler..." -ForegroundColor Cyan

# 1. Create Morning Task (07:00 AM)
schtasks /create /tn "YouTubeAutopilot_Morning" /tr "wscript.exe `"$vbsMorning`"" /sc daily /st 07:00 /f | Out-Null
Write-Host "Created Morning Task: YouTubeAutopilot_Morning (07:00 AM)" -ForegroundColor Green

# 2. Create Evening Task (06:00 PM / 18:00)
schtasks /create /tn "YouTubeAutopilot_Evening" /tr "wscript.exe `"$vbsEvening`"" /sc daily /st 18:00 /f | Out-Null
Write-Host "Created Evening Task: YouTubeAutopilot_Evening (06:00 PM)" -ForegroundColor Green

# 3. Configure Battery, Wake-up, and StartWhenAvailable (Catch-Up) Settings
$tasks = @("YouTubeAutopilot_Morning", "YouTubeAutopilot_Evening")
foreach ($t in $tasks) {
    try {
        $task = Get-ScheduledTask -TaskName $t
        $task.Settings.DisallowStartIfOnBatteries = $false
        $task.Settings.StopIfGoingOnBatteries = $false
        $task.Settings.StartWhenAvailable = $true
        $task.Settings.WakeToRun = $true
        $task.Settings.ExecutionTimeLimit = "PT1H"
        Set-ScheduledTask -InputObject $task | Out-Null
        Write-Host "Configured 24/7 background settings for $t (wake, battery, missed-run catchup)" -ForegroundColor Green
    } catch {
        Write-Host "Warning setting extended flags on ${t}: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

Write-Host "`nAutomation setup complete! Your Shorts will publish daily at 07:00 AM and 06:00 PM IST with zero manual intervention." -ForegroundColor Cyan
