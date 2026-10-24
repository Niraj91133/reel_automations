Set WshShell = CreateObject("WScript.Shell")
startupFolder = WshShell.SpecialFolders("Startup")
Set shortcut = WshShell.CreateShortcut(startupFolder & "\InstagramReelController.lnk")
shortcut.TargetPath = "wscript.exe"
shortcut.Arguments = Chr(34) & "C:\Users\DHEERAJ\OneDrive\Desktop\Insta Video\run_background_controller.vbs" & Chr(34)
shortcut.WorkingDirectory = "C:\Users\DHEERAJ\OneDrive\Desktop\Insta Video"
shortcut.WindowStyle = 7
shortcut.Save