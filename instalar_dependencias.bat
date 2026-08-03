@echo off
echo ====================================================
echo INSTALADOR DE DEPENDENCIAS - ASISTENTE FINANCIERO
echo ====================================================
echo.

:: Intentar con python
python -c "import sys; print(sys.version)" >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo [OK] Python encontrado usando el comando 'python'.
    python -m pip install -r requirements.txt
    goto end
)

:: Intentar con py
py -c "import sys; print(sys.version)" >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo [OK] Python encontrado usando el comando 'py'.
    py -m pip install -r requirements.txt
    goto end
)

:: Intentar con python3
python3 -c "import sys; print(sys.version)" >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo [OK] Python encontrado usando el comando 'python3'.
    python3 -m pip install -r requirements.txt
    goto end
)

echo [ERROR] No se pudo encontrar Python en el sistema. 
echo Por favor asegurate de tener Python instalado y agregado al PATH (variables de entorno).
pause
exit /b 1

:end
echo.
echo ====================================================
echo Instalacion completada exitosamente.
echo ====================================================
pause
exit /b 0
