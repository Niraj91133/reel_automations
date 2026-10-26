Set WshShell = CreateObject("WScript.Shell")
startupFolder = WshShell.SpecialFolders("Startup")
Set shortcut = WshShell.CreateShortcut(startupFolder & "\InstagramReelController.lnk")
shortcut.TargetPath = "wscript.exe"
shortcut.Arguments = Chr(34) & "D:\Bittu - Soft\Client Project\reel_automations-main\run_background_controller.vbs" & Chr(34)
shortcut.WorkingDirectory = "D:\Bittu - Soft\Client Project\reel_automations-main"
shortcut.WindowStyle = 7
shortcut.Save