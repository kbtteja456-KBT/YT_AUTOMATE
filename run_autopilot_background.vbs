Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\DELL\OneDrive\Desktop\yt"
WshShell.Run "cmd /c ""C:\Users\DELL\OneDrive\Desktop\yt\start_autopilot.bat""", 0, False
