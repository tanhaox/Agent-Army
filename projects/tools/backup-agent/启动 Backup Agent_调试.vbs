Set WshShell = CreateObject("WScript.Shell")

' 硬编码路径
scriptDir = "C:\AI-Agent-Local\projects\tools\backup-agent"

' 显示调试信息
MsgBox "即将启动 Backup Agent..." & vbCrLf & "目录: " & scriptDir

' 切换目录
On Error Resume Next
WshShell.CurrentDirectory = scriptDir

If Err.Number <> 0 Then
    MsgBox "切换目录失败: " & Err.Description
    WScript.Quit
End If

' 启动程序（False = 不等待程序完成）
command = "pythonw backup_agent.py --daemon --tray"
WshShell.Run command, 0, False

' 短暂等待，给程序启动时间
WScript.Sleep 2000

' 检查进程是否运行
Set proc = WshShell.Exec("tasklist /FI ""IMAGENAME eq pythonw.exe""")
output = proc.StdOut.ReadAll

If InStr(output, "pythonw.exe") > 0 Then
    MsgBox "启动成功！" & vbCrLf & "请在系统托盘查看 Backup Agent 图标"
Else
    MsgBox "启动失败！未找到 pythonw.exe 进程"
End If

Set WshShell = Nothing
