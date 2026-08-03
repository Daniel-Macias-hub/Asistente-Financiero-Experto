"""
Módulo de verificación de conectividad a Internet.
Determina si el sistema opera en modo online u offline.
"""
import socket


def hay_internet(host="8.8.8.8", port=53, timeout=3):
    """
    Verifica si hay conexión a Internet haciendo un socket connect
    al DNS público de Google.
    
    Args:
        host: Dirección IP a verificar.
        port: Puerto (53 = DNS).
        timeout: Tiempo máximo de espera en segundos.
    
    Returns:
        True si hay conexión, False si no.
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except (socket.error, OSError):
        return False


def modo_actual():
    """
    Retorna el modo de operación actual del sistema.
    
    Returns:
        "online" si hay Internet, "offline" si no.
    """
    from config import MODO_OFFLINE_FORZADO
    if MODO_OFFLINE_FORZADO:
        return "offline"
    return "online" if hay_internet() else "offline"
