# ApexOne Status Checker タスクスケジューラー設定スクリプト
# 管理者権限で実行してください

# 文字化け対策: メインスクリプトで対応

param(
    [string]$TaskName = "ApexOne Status Checker",
    [string]$Description = "毎日10時にApexOne Status Checkerを実行",
    [string]$StartTime = "10:00",
    [string]$BatchFilePath = "C:\Users\1040120\ApexOne_status_checker\run_status_checker.bat"
)

Write-Host "========================================" -ForegroundColor Green
Write-Host "ApexOne Status Checker タスクスケジューラー設定" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# 管理者権限チェック
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ このスクリプトは管理者権限で実行する必要があります" -ForegroundColor Red
    Write-Host "💡 PowerShellを管理者として実行してください" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "✅ 管理者権限を確認しました" -ForegroundColor Green

# バッチファイルの存在確認
if (-NOT (Test-Path $BatchFilePath)) {
    Write-Host "❌ バッチファイルが見つかりません: $BatchFilePath" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "✅ バッチファイルを確認しました: $BatchFilePath" -ForegroundColor Green

# 既存のタスクを削除（存在する場合）
try {
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "🔄 既存のタスクを削除中: $TaskName" -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "✅ 既存のタスクを削除しました" -ForegroundColor Green
    }
} catch {
    Write-Host "ℹ️ 既存のタスクは存在しません" -ForegroundColor Blue
}

# タスクのアクション設定
$action = New-ScheduledTaskAction -Execute $BatchFilePath -WorkingDirectory "C:\Users\1040120\ApexOne_status_checker"

# タスクのトリガー設定（毎日10時）
$trigger = New-ScheduledTaskTrigger -Daily -At $StartTime

# タスクの設定
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

# タスクの作成
try {
    $task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Description $Description
    
    # タスクを登録
    Register-ScheduledTask -TaskName $TaskName -InputObject $task -User "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    
    Write-Host "✅ タスクスケジューラーに登録しました！" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 登録内容:" -ForegroundColor Cyan
    Write-Host "  タスク名: $TaskName" -ForegroundColor White
    Write-Host "  実行時刻: 毎日 $StartTime" -ForegroundColor White
    Write-Host "  実行ファイル: $BatchFilePath" -ForegroundColor White
    Write-Host "  説明: $Description" -ForegroundColor White
    Write-Host ""
    Write-Host "🔍 確認方法:" -ForegroundColor Cyan
    Write-Host "  1. タスクスケジューラーを開く" -ForegroundColor White
    Write-Host "  2. タスクスケジューラーライブラリ → $TaskName" -ForegroundColor White
    Write-Host "  3. プロパティで詳細設定を確認" -ForegroundColor White
    
} catch {
    Write-Host "❌ タスクの登録に失敗しました: $($_.Exception.Message)" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "🎉 設定完了！" -ForegroundColor Green
Write-Host "💡 毎日10時に自動実行されます" -ForegroundColor Yellow
pause
