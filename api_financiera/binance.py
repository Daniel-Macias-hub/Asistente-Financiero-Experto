"""
Cliente para la API pública de Binance.
Obtiene precios en tiempo real y estadísticas de 24 horas.
No requiere autenticación para datos públicos de mercado.
Documentación: https://binance-docs.github.io/apidocs/spot/en/
"""
import requests
from config import BINANCE_BASE_URL, CRYPTO_MAP


def _obtener_binance_symbol(nombre):
    """Convierte nombre local a símbolo de Binance (ej. BTCUSDT)."""
    nombre_lower = nombre.lower().strip()
    if nombre_lower in CRYPTO_MAP:
        return CRYPTO_MAP[nombre_lower]["binance"]
    # Intentar construirlo
    return nombre.upper() + "USDT"


def obtener_precio_ticker(nombre):
    """
    Obtiene el precio actual de una criptomoneda.
    
    Args:
        nombre: Nombre de la criptomoneda (ej. "bitcoin").
    
    Returns:
        float con el precio en USD, o None si hay error.
    """
    symbol = _obtener_binance_symbol(nombre)
    
    try:
        url = f"{BINANCE_BASE_URL}/ticker/price"
        params = {"symbol": symbol}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data.get("price", 0))
    except (requests.RequestException, ValueError) as e:
        print(f"[Binance] Error al obtener precio de {nombre}: {e}")
        return None


def obtener_24h_stats(nombre):
    """
    Obtiene estadísticas de las últimas 24 horas de un par de trading.
    
    Args:
        nombre: Nombre de la criptomoneda.
    
    Returns:
        dict con precio, high, low, volumen, cambio_porcentaje.
        None si hay error.
    """
    symbol = _obtener_binance_symbol(nombre)
    
    try:
        url = f"{BINANCE_BASE_URL}/ticker/24hr"
        params = {"symbol": symbol}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return {
            "precio": float(data.get("lastPrice", 0)),
            "precio_apertura": float(data.get("openPrice", 0)),
            "high_24h": float(data.get("highPrice", 0)),
            "low_24h": float(data.get("lowPrice", 0)),
            "volumen": float(data.get("volume", 0)),
            "cambio_porcentaje": float(data.get("priceChangePercent", 0)),
            "trades_count": int(data.get("count", 0)),
        }
    except (requests.RequestException, ValueError) as e:
        print(f"[Binance] Error al obtener stats 24h de {nombre}: {e}")
        return None
