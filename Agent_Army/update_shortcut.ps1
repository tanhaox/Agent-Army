$TargetFile = "C:\AI-Agent-Local\Agent_Army\启动最新修复版.bat"
$ShortcutFile = "C:\Users\tanha\Desktop\Agent Army Web.lnk"
$WorkDir = "C:\AI-Agent-Local\Agent_Army"
$Description = "Agent Army Web v2.0 - Latest Fixed Version"
$Icon = "C:\AI-Agent-Local\Agent_Army\启动最新修复版.bat,0"

$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($ShortcutFile)

$Shortcut.TargetPath = $TargetFile
$Shortcut.WorkingDirectory = $WorkDir
$Shortcut.Description = $Description
$Shortcut.IconLocation = $Icon

$Shortcut.Save()

Write-Host "Shortcut updated successfully!" -ForegroundColor Green
Write-Host "Location: $ShortcutFile"
