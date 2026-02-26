Set WshShell = CreateObject("WScript.Shell")
' 使用完整路径
cmd = "C:\Python313\pythonw.exe C:\AI-Agent-Local\projects\tools\backup-agent\backup_agent.py --daemon --tray"
' 启动程序（隐藏窗口，不等待）
WshShell.Run cmd, 0, False
Set WshShell = Nothing
