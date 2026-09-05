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
        Write-Host "Updated settings for $t successfully!" -ForegroundColor Green
    } catch {
        Write-Host "Error updating ${t}: $($_.Exception.Message)" -ForegroundColor Red
    }
}
