# Script de Sincronización Triple: GitHub <-> Laptop Workspace <-> USB Backup
param (
    [string]$TargetUsbDrive = ""
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Sincronizador de Trabajo - Asistente Financiero Experto " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$WorkspacePath = "D:\INTELIGENCIA_DE_NEGOCIOS\asistente_financiero"
Set-Location -Path $WorkspacePath

# 1. Verificar Estado de Git Local
Write-Host "`n[1/3] Verificando estado del repositorio Git..." -ForegroundColor Yellow
git status

# 2. Deteccion de Unidad USB
if ([string]::IsNullOrWhiteSpace($TargetUsbDrive)) {
    Write-Host "`n[2/3] Buscando unidades USB extraibles..." -ForegroundColor Yellow
    $Drives = Get-Volume | Where-ObjectType { $_.DriveType -eq 'Removable' -and $_.DriveLetter }
    if ($Drives.Count -gt 0) {
        $TargetUsbDrive = "$($Drives[0].DriveLetter):\"
        Write-Host "Unidad USB detectada automaticamente: $TargetUsbDrive" -ForegroundColor Green
    } else {
        Write-Host "No se detecto unidad USB extraible automaticamente." -ForegroundColor Yellow
        $TargetUsbDrive = Read-Host "Por favor ingrese la letra de la unidad USB (ejemplo E:\): "
    }
}

if (-not (Test-Path $TargetUsbDrive)) {
    Write-Host "[ERROR] La ruta '$TargetUsbDrive' no es accesible. Omite el respaldo en USB por ahora." -ForegroundColor Red
    exit 1
}

$BackupFolder = Join-Path -Path $TargetUsbDrive -ChildPath "Asistente_Financiero_Backup"
if (-not (Test-Path $BackupFolder)) {
    New-Item -Path $BackupFolder -ItemType Directory | Out-Null
    Write-Host "Carpeta de respaldo creada en: $BackupFolder" -ForegroundColor Green
}

# 3. Respaldo Diferencial hacia la USB (Excluyendo __pycache__ y venv)
Write-Host "`n[3/3] Copiando archivos actualizados a la unidad USB ($BackupFolder)..." -ForegroundColor Yellow
robocopy $WorkspacePath $BackupFolder /MIR /XD __pycache__ venv .git /NJH /NJS /NDL /NC /NS

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " Respaldo en USB completado exitosamente." -ForegroundColor Green
Write-Host " Recuerda hacer push a GitHub cuando desees sincronizar remoto:" -ForegroundColor Cyan
Write-Host "   git push origin Pruebas-Exitosas-Y-Port" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Green
