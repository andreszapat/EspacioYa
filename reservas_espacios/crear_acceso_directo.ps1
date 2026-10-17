$carpeta = Split-Path -Parent $MyInvocation.MyCommand.Path
$escritorio = [Environment]::GetFolderPath('Desktop')
$pythonw = Join-Path $carpeta '.venv\Scripts\pythonw.exe'

$shell = New-Object -ComObject WScript.Shell
$acceso = $shell.CreateShortcut((Join-Path $escritorio 'Reservas de Espacios.lnk'))
$acceso.TargetPath = $pythonw
$acceso.Arguments = '"' + (Join-Path $carpeta 'desktop.py') + '"'
$acceso.WorkingDirectory = $carpeta
$acceso.IconLocation = (Join-Path $carpeta 'reservas.ico')
$acceso.Description = 'Sistema de Reservas de Espacios (puerto 5050)'
$acceso.Save()

Write-Host "Acceso directo creado en: $escritorio"
