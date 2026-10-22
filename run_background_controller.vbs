Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\DHEERAJ\OneDrive\Desktop\Insta Video"
WshShell.Run "pythonw telegram_controller.py", 0, False
