@echo off
REM ApexOne Status Checker 実行バッチファイル
REM タスクスケジューラー用

echo ========================================
echo ApexOne Status Checker 開始
echo 実行日時: %date% %time%
echo ========================================

REM 作業ディレクトリに移動
cd /d "C:\Users\1040120\ApexOne_status_checker"

REM Pythonスクリプトを実行
echo Pythonスクリプトを実行中...
"C:\Users\1040120\AppData\Local\Programs\Python\Python311\python.exe" ApexOne_status_checker.py

REM 実行結果を確認
if %errorlevel% equ 0 (
    echo ========================================
    echo 実行完了: 成功
    echo ========================================
) else (
    echo ========================================
    echo 実行完了: エラー (終了コード: %errorlevel%)
    echo ========================================
)

REM ログファイルの内容を表示
if exist "apexone_status_log.csv" (
    echo.
    echo 最新のログ内容:
    echo ----------------------------------------
    powershell -Command "Get-Content 'apexone_status_log.csv' -Tail 3 | ForEach-Object { Write-Host $_ }"
    echo ----------------------------------------
)

echo.
echo 実行完了時刻: %date% %time%
pause
