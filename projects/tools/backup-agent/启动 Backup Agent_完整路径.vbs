Set WshShell = CreateObject("WScript.Shell")

' 设置工作目录
WshShell.CurrentDirectory = "C:\AI-Agent-Local\projects\tools\backup-agent"

' 使用完整路径启动 pythonw.exe
pythonwPath = "C:\Python313\pythonw.exe"
scriptPath = "C:\AI-Agent-Local\projects\tools\backup-agent\backup_agent.py"

' 构建命令
command = """" & pythonwPath & """ """ & scriptPath & """ --daemon --tray"

' 启动程序（隐藏窗口，不等待）
WshShell.Run command, 0, False

Set WshShell = Nothing
