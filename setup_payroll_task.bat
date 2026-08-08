@echo off
echo =======================================================
echo Setting up Daily Payroll Automation for RAC ERP
echo =======================================================
echo.

:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Administrator privileges detected. Proceeding...
) else (
    echo [ERROR] Please run this script as Administrator.
    echo Right-click on setup_payroll_task.bat and select "Run as administrator".
    pause
    exit /b 1
)

:: Create the scheduled task using PowerShell
set TASK_NAME=RAC_ERP_Daily_Payroll
set PROJECT_DIR=d:\Preject\rac-erp-04082026

echo Creating Scheduled Task "%TASK_NAME%" to run daily at 1:00 AM...

powershell -Command "$action = New-ScheduledTaskAction -Execute 'python' -Argument 'manage.py auto_generate_payroll' -WorkingDirectory '%PROJECT_DIR%'; $trigger = New-ScheduledTaskTrigger -Daily -At 1:00AM; Register-ScheduledTask -Action $action -Trigger $trigger -TaskName '%TASK_NAME%' -Description 'Auto generate payroll for RAC ERP daily at 1 AM' -User 'NT AUTHORITY\SYSTEM' -Force"

if %errorLevel% == 0 (
    echo.
    echo [SUCCESS] Task created successfully! The payroll will now automatically update every night at 1:00 AM.
) else (
    echo.
    echo [FAILED] Failed to create the scheduled task.
)

pause
