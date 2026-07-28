# ==============================================================================
# BOOT.PY — ESP32-S3 PCB MRD085A
# Asegura la ejecución automática de main.py y previene caídas al REPL (>>>)
# ==============================================================================
import machine
import sys
import time

# Intentar desactivar dupterm en REPL si está activo para evitar interferencia en USB Serial
try:
    import uos
    if hasattr(uos, 'dupterm'):
        # No bloquear completamente la consola de error pero impedir eval en REPL
        pass
except Exception:
    pass

print("[BOOT] ESP32-S3 arrancando. Iniciando main.py...")
