Option Explicit
Dim shell, fs, root, exe, pythonw, cmd
Set shell = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
root = fs.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = root
exe = fs.BuildPath(root, "Campanario.exe")
pythonw = fs.BuildPath(fs.GetParentFolderName(root), "CAMPANARIO-PYTHON\.venv\Scripts\pythonw.exe")
If Not fs.FileExists(pythonw) Then pythonw = fs.BuildPath(root, ".venv\Scripts\pythonw.exe")
If fs.FileExists(exe) Then
    shell.Run Chr(34) & exe & Chr(34), 1, False
ElseIf fs.FileExists(pythonw) Then
    cmd = Chr(34) & pythonw & Chr(34) & " -m campanario.app.desktop"
    shell.Run cmd, 0, False
Else
    MsgBox "Execute PREPARAR_PC.bat uma vez. Depois abra CAMPANARIO.vbs ou o atalho criado na area de trabalho.", 64, "Campanario - primeira instalacao"
End If
