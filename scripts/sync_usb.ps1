# Script PowerShell de respaldo diferencial hacia USB y almacenamiento local
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Sincronizador de Trabajo - Asistente Financiero Experto " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$SourceDir = "D:\INTELIGENCIA_DE_NEGOCIOS\asistente_financiero"
$LocalBackupDir = "D:\INTELIGENCIA_DE_NEGOCIOS\BACKUP_ASISTENTE_FINANCIERO"

# 1. Respaldo Local en PC
Write-Host "`n[1/3] Creando respaldo local en PC: $LocalBackupDir..." -ForegroundColor Yellow
if (-not (Test-Path $LocalBackupDir)) {
    New-Item -ItemType Directory -Path $LocalBackupDir -Force | Out-Null
}
robocopy $SourceDir $LocalBackupDir /MIR /XD .git .venv __pycache__ .gemini | Out-Null
Write-Host "[OK] Respaldo local sincronizado correctamente." -ForegroundColor Green

# 2. Respaldo en USB Extraíble
Write-Host "`n[2/3] Buscando unidades USB extraíbles..." -ForegroundColor Yellow
$UsbDrives = Get-WmiObject Win32_Volume | Where-Object { $_.DriveType -eq 2 -and $_.DriveLetter }

if ($UsbDrives) {
    foreach ($drive in $UsbDrives) {
        $usbPath = Join-Path -Path $drive.DriveLetter -ChildPath "ASISTENTE_FINANCIERO_BACKUP"
        Write-Host "[USB] Sincronizando hacia: $usbPath ..." -ForegroundColor Cyan
        if (-not (Test-Path $usbPath)) {
            New-Item -ItemType Directory -Path $usbPath -Force | Out-Null
        }
        robocopy $SourceDir $usbPath /MIR /XD .git .venv __pycache__ .gemini | Out-Null
        Write-Host "[OK] Respaldo en USB ($($drive.DriveLetter)) completado." -ForegroundColor Green
    }
} else {
    Write-Host "[AVISO] No se detectó unidad USB insertada actualmente. Respaldo en PC realizado." -ForegroundColor Yellow
}

# 3. Estado Git
Write-Host "`n[3/3] Estado del repositorio Git..." -ForegroundColor Yellow
git status
