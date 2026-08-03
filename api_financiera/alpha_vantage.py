"""
Cliente para la API de Alpha Vantage.
Obtiene precios de acciones e índices bursátiles.
Requiere API key gratuita: https://www.alphavantage.co/support/#api-key
Documentación: https://www.alphavantage.co/documentation/
"""
import requests
from config import ALPHA_VANTAGE_BASE_URL, ALPHA_VANTAGE_API_KEY


def obtener_precio_accion(symbol):
    """
    Obtiene el precio actual de una acción o ETF.
    
    Args:
        symbol: Símbolo del ticker (ej. "AAPL", "MSFT", "SPY").
    
    Returns:
        dict con precio, apertura, high, low, volumen, cambio.
        None si hay error o no hay API key configurada.
    """
    if not ALPHA_VANTAGE_API_KEY:
        print("[Alpha Vantage] API key no configurada. Establece la variable de entorno ALPHA_VANTAGE_API_KEY.")
        return None
    
    try:
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol.upper(),
            "apikey": ALPHA_VANTAGE_API_KEY,
        }
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        quote = data.get("Global Quote", {})
        if not quote:
            return None
        
        return {
            "simbolo": quote.get("01. symbol", symbol),
            "precio": float(quote.get("05. price", 0)),
            "apertura": float(quote.get("02. open", 0)),
            "high": float(quote.get("03. high", 0)),
            "low": float(quote.get("04. low", 0)),
            "volumen": int(quote.get("06. volume", 0)),
            "cambio": float(quote.get("09. change", 0)),
            "cambio_porcentaje": quote.get("10. change percent", "0%"),
            "dia_anterior": float(quote.get("08. previous close", 0)),
        }
    except (requests.RequestException, ValueError) as e:
        print(f"[Alpha Vantage] Error al obtener {symbol}: {e}")
        return None


def obtener_indice(symbol):
    """
    Obtiene datos de un índice bursátil.
    Usa la misma función GLOBAL_QUOTE (los ETFs de índices como SPY, QQQ funcionan).
    
    Args:
        symbol: Símbolo del ETF del índice (ej. "SPY" para S&P 500, "QQQ" para NASDAQ).
    
    Returns:
        dict con los mismos campos que obtener_precio_accion.
    """
    return obtener_precio_accion(symbol)


def buscar_ticker(keywords):
    """
    Busca tickers de acciones por nombre.
    
    Args:
        keywords: Texto de búsqueda (ej. "Apple", "Microsoft").
    
    Returns:
        Lista de dicts con simbolo, nombre, tipo, region.
        Lista vacía si hay error.
    """
    if not ALPHA_VANTAGE_API_KEY:
        return []
    
    try:
        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": keywords,
            "apikey": ALPHA_VANTAGE_API_KEY,
        }
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        resultados = []
        for match in data.get("bestMatches", []):
            resultados.append({
                "simbolo": match.get("1. symbol", ""),
                "nombre": match.get("2. name", ""),
                "tipo": match.get("3. type", ""),
                "region": match.get("4. region", ""),
            })
        return resultados
    except requests.RequestException as e:
        print(f"[Alpha Vantage] Error en búsqueda: {e}")
        return []
