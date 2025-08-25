# ApexOne Status Checker Task Scheduler Setup Script
# Run with Administrator privileges

param(
    [string]$TaskName = "ApexOne Status Checker",
    [string]$Description = "Execute ApexOne Status Checker daily at 10:00",
    [string]$StartTime = "10:00",
    [string]$BatchFilePath = "C:\Users\1040120\ApexOne_status_checker\run_status_checker.bat"
)

Write-Host "========================================" -ForegroundColor Green
Write-Host "ApexOne Status Checker Task Scheduler Setup" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Check Administrator privileges
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ This script requires Administrator privileges" -ForegroundColor Red
    Write-Host "💡 Please run PowerShell as Administrator" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "✅ Administrator privileges confirmed" -ForegroundColor Green

# Check if batch file exists
if (-NOT (Test-Path $BatchFilePath)) {
    Write-Host "❌ Batch file not found: $BatchFilePath" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "✅ Batch file confirmed: $BatchFilePath" -ForegroundColor Green

# Remove existing task if it exists
try {
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "🔄 Removing existing task: $TaskName" -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "✅ Existing task removed" -ForegroundColor Green
    }
} catch {
    Write-Host "ℹ️ No existing task found" -ForegroundColor Blue
}

# Create task action
$action = New-ScheduledTaskAction -Execute $BatchFilePath -WorkingDirectory "C:\Users\1040120\ApexOne_status_checker"

# Create task trigger (daily at 10:00)
$trigger = New-ScheduledTaskTrigger -Daily -At $StartTime

# Create task settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

# Create and register task
try {
    $task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Description $Description
    
    # Register the task
    Register-ScheduledTask -TaskName $TaskName -InputObject $task -User "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    
    Write-Host "✅ Task registered in Task Scheduler!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Registration details:" -ForegroundColor Cyan
    Write-Host "  Task Name: $TaskName" -ForegroundColor White
    Write-Host "  Execution Time: Daily at $StartTime" -ForegroundColor White
    Write-Host "  Execution File: $BatchFilePath" -ForegroundColor White
    Write-Host "  Description: $Description" -ForegroundColor White
    Write-Host ""
    Write-Host "🔍 Verification method:" -ForegroundColor Cyan
    Write-Host "  1. Open Task Scheduler" -ForegroundColor White
    Write-Host "  2. Task Scheduler Library → $TaskName" -ForegroundColor White
    Write-Host "  3. Check detailed settings in Properties" -ForegroundColor White
    
} catch {
    Write-Host "❌ Task registration failed: $($_.Exception.Message)" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "🎉 Setup complete!" -ForegroundColor Green
Write-Host "💡 Will execute automatically daily at 10:00" -ForegroundColor Yellow
pause
