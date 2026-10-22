Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\DHEERAJ\OneDrive\Desktop\Insta Video"
WshShell.Run Chr(34) & "C:\Users\DHEERAJ\AppData\Local\Microsoft\WindowsApps\python.exe" & Chr(34) & " telegram_controller.py", 0, False
