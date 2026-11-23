Option Explicit
Dim fs, shell, root, bat
Set fs = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
root = fs.GetParentFolderName(WScript.ScriptFullName)
bat = fs.BuildPath(root, "CAMPANARIO.bat")
shell.Run "cmd.exe /c " & Chr(34) & Chr(34) & bat & Chr(34) & Chr(34), 1, False
