Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\DELL\OneDrive\Desktop\yt"
WshShell.Run """C:\Users\DELL\AppData\Local\Programs\Python\Python314\python.exe"" run_slot_cli.py --slot 2 --include-tenants", 0, True
