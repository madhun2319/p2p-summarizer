# Setup a Windows Scheduled Task (Cron job) to run every Monday at 8:00 AM
$TaskName = "BioPulse_Weekly_Cron"
$ScriptPath = Join-Path $PSScriptRoot "run_weekly.ps1"

$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"$ScriptPath`""
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 8:00AM

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Description "Runs BioPulse AI weekly PDB ingestion and newsletter synthesis." -Force

Write-Host "✅ Scheduled Task '$TaskName' registered successfully!" -ForegroundColor Green
Write-Host "📅 It will run automatically every Monday at 08:00 AM." -ForegroundColor Cyan
