Set WshShell = CreateObject("WScript.Shell")
' 使用 python 但隐藏窗口
WshShell.Run "C:\Python313\python.exe C:\AI-Agent-Local\projects\tools\backup-agent\backup_agent.py --daemon --tray", 0, False
Set WshShell = Nothing
