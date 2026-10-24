import os
import sys
import subprocess
vbs_script = (
    'Set WshShell = CreateObject("WScript.Shell")\n'
    'startupFolder = WshShell.SpecialFolders("Startup")\n'
    'Set shortcut = WshShell.CreateShortcut(startupFolder & "\\InstagramReelController.lnk")\n'
    'shortcut.TargetPath = "wscript.exe"\n'
    'shortcut.Arguments = Chr(34) & "C:\\Users\\DHEERAJ\\OneDrive\\Desktop\\Insta Video\\run_background_controller.vbs" & Chr(34)\n'
    'shortcut.WorkingDirectory = "C:\\Users\\DHEERAJ\\OneDrive\\Desktop\\Insta Video"\n'
    'shortcut.WindowStyle = 7\n'
    'shortcut.Save\n'
)

with open("create_startup_shortcut.vbs", "w") as f:
    f.write(vbs_script.strip())

subprocess.run(["cscript", "//nologo", "create_startup_shortcut.vbs"])
print("Startup shortcut created!")
