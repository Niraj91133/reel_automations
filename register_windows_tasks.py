import os
import sys
import subprocess

sys.stdout.reconfigure(encoding='utf-8')

def setup_tasks():
    cwd = r"C:\Users\DHEERAJ\OneDrive\Desktop\Insta Video"
    
    # 1. PowerShell script to register Daily 10:00 PM Task
    ps_daily_task = f"""
    Unregister-ScheduledTask -TaskName "ReelAutomation_Daily9AM" -Confirm:$false -ErrorAction SilentlyContinue
    $Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument '/c python run_all_daily.py 10 >> daily_10pm.log 2>&1' -WorkingDirectory "{cwd}"
    $Trigger = New-ScheduledTaskTrigger -Daily -At 10:00PM
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -WakeToRun -ExecutionTimeLimit (New-TimeSpan -Hours 2)
    Register-ScheduledTask -TaskName "ReelAutomation_Daily10PM" -Action $Action -Trigger $Trigger -Settings $Settings -Description "Daily 10:00 PM Instagram Reel Automation" -Force
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
        print("✅ ReelAutomation_Daily10PM successfully scheduled for 10:00 PM daily!")
    else:
        print("⚠️ Daily 10PM Task Warning:", res1.stderr or res1.stdout)

    res2 = subprocess.run(["powershell", "-NoProfile", "-Command", ps_controller_task], capture_output=True, text=True)
    if res2.returncode == 0:
        print("✅ ReelAutomation_TelegramController successfully registered to auto-start on logon!")
    else:
        print("⚠️ Controller Task Warning:", res2.stderr or res2.stdout)

if __name__ == '__main__':
    setup_tasks()
