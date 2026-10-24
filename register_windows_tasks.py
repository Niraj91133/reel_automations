import os
import sys
import subprocess

sys.stdout.reconfigure(encoding='utf-8')

def setup_tasks():
    cwd = r"C:\Users\DHEERAJ\OneDrive\Desktop\Insta Video"
    
    # 1. PowerShell script to register Daily 9:00 AM Task
    ps_daily_task = f"""
    $Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument '/c python run_all_daily.py 10 >> daily_9am.log 2>&1' -WorkingDirectory "{cwd}"
    $Trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -WakeToRun -ExecutionTimeLimit (New-TimeSpan -Hours 2)
    Register-ScheduledTask -TaskName "ReelAutomation_Daily9AM" -Action $Action -Trigger $Trigger -Settings $Settings -Description "Daily 9:00 AM Instagram Reel Automation" -Force
    """

    # 2. PowerShell script to register 24/7 Telegram Controller at User Logon
    ps_controller_task = f"""
    $Action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument '"{cwd}\\run_background_controller.vbs"' -WorkingDirectory "{cwd}"
    $Trigger = New-ScheduledTaskTrigger -AtLogOn
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit 0
    Register-ScheduledTask -TaskName "ReelAutomation_TelegramController" -Action $Action -Trigger $Trigger -Settings $Settings -Description "24/7 Telegram Command Controller for Reels" -Force
    """

    print("Registering Windows Scheduled Tasks...")
    res1 = subprocess.run(["powershell", "-NoProfile", "-Command", ps_daily_task], capture_output=True, text=True)
    if res1.returncode == 0:
        print("✅ ReelAutomation_Daily9AM successfully scheduled for 9:00 AM daily!")
    else:
        print("⚠️ Daily 9AM Task Warning:", res1.stderr or res1.stdout)

    res2 = subprocess.run(["powershell", "-NoProfile", "-Command", ps_controller_task], capture_output=True, text=True)
    if res2.returncode == 0:
        print("✅ ReelAutomation_TelegramController successfully registered to auto-start on logon!")
    else:
        print("⚠️ Controller Task Warning:", res2.stderr or res2.stdout)

if __name__ == '__main__':
    setup_tasks()
