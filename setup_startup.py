import os
import sys
import subprocess
current_dir = os.path.dirname(os.path.abspath(__file__))
vbs_path = os.path.join(current_dir, "run_background_controller.vbs")

vbs_script = (
    'Set WshShell = CreateObject("WScript.Shell")\n'
    'startupFolder = WshShell.SpecialFolders("Startup")\n'
    'Set shortcut = WshShell.CreateShortcut(startupFolder & "\\InstagramReelController.lnk")\n'
    'shortcut.TargetPath = "wscript.exe"\n'
    f'shortcut.Arguments = Chr(34) & "{vbs_path}" & Chr(34)\n'
    f'shortcut.WorkingDirectory = "{current_dir}"\n'
    'shortcut.WindowStyle = 7\n'
    'shortcut.Save\n'
)

with open("create_startup_shortcut.vbs", "w") as f:
    f.write(vbs_script.strip())

subprocess.run(["cscript", "//nologo", "create_startup_shortcut.vbs"])
print("Startup shortcut created!")
