"""
Cliente para la API de CoinGecko.
Obtiene precios, capitalización, volumen y ranking de criptomonedas.
API gratuita: no requiere API key para funciones básicas.
Documentación: https://www.coingecko.com/en/api/documentation
"""
import requests
from config import COINGECKO_BASE_URL, CRYPTO_MAP


def _obtener_coingecko_id(nombre):
    """Convierte nombre local a CoinGecko ID."""
    nombre_lower = nombre.lower().strip()
    if nombre_lower in CRYPTO_MAP:
        return CRYPTO_MAP[nombre_lower]["coingecko_id"]
    # Intentar búsqueda directa
    return nombre_lower


def obtener_info_cripto(nombre):
    """
    Obtiene información completa de una criptomoneda.
    
    Args:
        nombre: Nombre de la criptomoneda (ej. "bitcoin", "ethereum").
    
    Returns:
        dict con precio_usd, precio_mxn, market_cap, volumen_24h, 
        cambio_24h, ranking, nombre, simbolo. 
        None si hay error.
    """
    coingecko_id = _obtener_coingecko_id(nombre)
    
    try:
        url = f"{COINGECKO_BASE_URL}/coins/{coingecko_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
            "sparkline": "false"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        market = data.get("market_data", {})
        
        return {
            "nombre": data.get("name", nombre),
            "simbolo": data.get("symbol", "").upper(),
            "precio_usd": market.get("current_price", {}).get("usd", 0),
            "precio_mxn": market.get("current_price", {}).get("mxn", 0),
            "market_cap": market.get("market_cap", {}).get("usd", 0),
            "volumen_24h": market.get("total_volume", {}).get("usd", 0),
            "cambio_24h": market.get("price_change_percentage_24h", 0),
            "ranking": data.get("market_cap_rank", 0),
            "descripcion": data.get("description", {}).get("es", "") or data.get("description", {}).get("en", ""),
            "imagen": data.get("image", {}).get("large", ""),
        }
    except requests.RequestException as e:
        print(f"[CoinGecko] Error al consultar {nombre}: {e}")
        return None


def obtener_top_criptos(n=12):
    """
    Obtiene las top N criptomonedas por capitalización de mercado.
    
    Args:
        n: Cantidad de criptomonedas a obtener (default 12).
    
    Returns:
        Lista de dicts con nombre, simbolo, precio, market_cap, cambio_24h, ranking.
        Lista vacía si hay error.
    """
    try:
        url = f"{COINGECKO_BASE_URL}/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": n,
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "24h"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        resultados = []
        for coin in data:
            resultados.append({
                "nombre": coin.get("name", ""),
                "simbolo": coin.get("symbol", "").upper(),
                "precio_usd": coin.get("current_price", 0),
                "market_cap": coin.get("market_cap", 0),
                "volumen_24h": coin.get("total_volume", 0),
                "cambio_24h": coin.get("price_change_percentage_24h", 0),
                "ranking": coin.get("market_cap_rank", 0),
                "imagen": coin.get("image", ""),
            })
        return resultados
    except requests.RequestException as e:
        print(f"[CoinGecko] Error al obtener top criptos: {e}")
        return []


def obtener_precio_simple(nombre):
    """
    Obtiene solo el precio actual de una criptomoneda (request más ligero).
    
    Args:
        nombre: Nombre de la criptomoneda.
    
    Returns:
        dict con precio_usd y precio_mxn, o None si hay error.
    """
    coingecko_id = _obtener_coingecko_id(nombre)
    
    try:
        url = f"{COINGECKO_BASE_URL}/simple/price"
        params = {
            "ids": coingecko_id,
            "vs_currencies": "usd,mxn",
            "include_24hr_change": "true",
            "include_market_cap": "true"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if coingecko_id in data:
            coin_data = data[coingecko_id]
            return {
                "precio_usd": coin_data.get("usd", 0),
                "precio_mxn": coin_data.get("mxn", 0),
                "cambio_24h": coin_data.get("usd_24h_change", 0),
                "market_cap": coin_data.get("usd_market_cap", 0),
            }
        return None
    except requests.RequestException as e:
        print(f"[CoinGecko] Error al obtener precio de {nombre}: {e}")
        return None
