Set WshShell = CreateObject("WScript.Shell")
' 使用硬编码的绝对路径，确保可靠
WshShell.CurrentDirectory = "C:\AI-Agent-Local\projects\tools\backup-agent"
' 启动 Backup Agent（后台运行，窗口隐藏）
WshShell.Run "pythonw backup_agent.py --daemon --tray", 0, False
Set WshShell = Nothing
