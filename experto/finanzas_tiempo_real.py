import yfinance as yf
from api_financiera.coingecko import obtener_info_cripto

CRYPTO_TICKER_MAP = {
    "BTC": "BTC-USD",
    "BITCOIN": "BTC-USD",
    "ETH": "ETH-USD",
    "ETHEREUM": "ETH-USD",
    "SOL": "SOL-USD",
    "SOLANA": "SOL-USD",
    "ADA": "ADA-USD",
    "CARDANO": "ADA-USD",
    "XRP": "XRP-USD"
}

def obtener_datos_accion(ticker: str) -> dict:
    """
    Obtiene información en tiempo real de una acción o criptousando yfinance o CoinGecko fallback.
    """
    ticker_clean = ticker.strip().upper()
    yf_ticker = CRYPTO_TICKER_MAP.get(ticker_clean, ticker_clean)

    # 1. Intentar consulta vía yfinance
    try:
        accion = yf.Ticker(yf_ticker)
        info = accion.info
        
        if "currentPrice" in info or "regularMarketPrice" in info:
            precio_actual = info.get("currentPrice") or info.get("regularMarketPrice")
            nombre_empresa = info.get("shortName") or info.get("longName", ticker_clean)
            moneda = info.get("currency", "USD")
            precio_anterior = info.get("previousClose", "No disponible")
            
            cambio_porcentaje = None
            if isinstance(precio_actual, (int, float)) and isinstance(precio_anterior, (int, float)):
                cambio_porcentaje = ((precio_actual - precio_anterior) / precio_anterior) * 100
                
            return {
                "ticker": ticker_clean,
                "nombre": nombre_empresa,
                "precio": precio_actual,
                "moneda": moneda,
                "cierre_anterior": precio_anterior,
                "cambio_porcentaje": cambio_porcentaje,
                "resumen": info.get("longBusinessSummary", "No hay resumen disponible.")
            }
    except Exception as e:
        print(f"[yfinance] Info no disponible para {yf_ticker}: {e}")

    # 2. Fallback Resiliente a CoinGecko para Criptomonedas
    try:
        info_cg = obtener_info_cripto(ticker_clean)
        if info_cg and info_cg.get("precio_usd", 0) > 0:
            return {
                "ticker": info_cg.get("simbolo", ticker_clean),
                "nombre": info_cg.get("nombre", ticker_clean),
                "precio": info_cg.get("precio_usd"),
                "moneda": "USD",
                "cierre_anterior": "N/A",
                "cambio_porcentaje": info_cg.get("cambio_24h"),
                "resumen": f"Ranking #{info_cg.get('ranking', 'N/A')} en CoinGecko"
            }
    except Exception as e:
        print(f"[CoinGecko Fallback] Error para {ticker_clean}: {e}")

    return None

def generar_respuesta_precio(ticker: str) -> tuple[str, list]:
    """
    Función de ayuda para usar desde el motor de inferencia.
    Retorna (texto_respuesta, log_inferencia)
    """
    log = [f"Consultando yfinance para el ticker: {ticker}"]
    datos = obtener_datos_accion(ticker)
    
    if not datos:
        log.append("No se pudieron obtener datos. Ticker inválido o error de red.")
        return f"Lo siento, no pude obtener datos para el ticker '{ticker}'. Verifica que esté escrito correctamente.", log
        
    log.append("Datos obtenidos exitosamente de Yahoo Finance.")
    
    cambio_str = ""
    if datos['cambio_porcentaje'] is not None:
        tendencia = "📈 subiendo" if datos['cambio_porcentaje'] >= 0 else "📉 bajando"
        cambio_str = f"({tendencia} un {abs(datos['cambio_porcentaje']):.2f}%)"
        
    respuesta = (
        f"📊 Datos en tiempo real para {datos['nombre']} ({datos['ticker']}):\n"
        f"• Precio Actual: {datos['precio']} {datos['moneda']} {cambio_str}\n"
        f"• Cierre Anterior: {datos['cierre_anterior']} {datos['moneda']}\n"
    )
    
    return respuesta, log
