Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\DHEERAJ\OneDrive\Desktop\Insta Video"
WshShell.Run "cmd /c python telegram_controller.py >> telegram_controller.log 2>&1", 0, False
