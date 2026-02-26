Set WshShell = CreateObject("WScript.Shell")
' 使用 Run 方法启动，第二个参数 0 表示隐藏窗口
WshShell.Run "pythonw ""C:\AI-Agent-Local\projects\tools\backup-agent\backup_agent.py"" --daemon --tray", 0, False
Set WshShell = Nothing
