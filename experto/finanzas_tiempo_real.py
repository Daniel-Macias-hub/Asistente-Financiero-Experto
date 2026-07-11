import yfinance as yf

def obtener_datos_accion(ticker: str) -> dict:
    """
    Obtiene información en tiempo real de una acción usando yfinance.
    Retorna un diccionario con los datos o None si ocurre un error/no se encuentra.
    """
    try:
        # Se remueven espacios y se convierte a mayúsculas por seguridad
        ticker = ticker.strip().upper()
        accion = yf.Ticker(ticker)
        info = accion.info
        
        if "currentPrice" not in info and "regularMarketPrice" not in info:
            # A veces yfinance falla o el ticker no existe
            return None
            
        precio_actual = info.get("currentPrice") or info.get("regularMarketPrice", "No disponible")
        nombre_empresa = info.get("shortName") or info.get("longName", ticker)
        moneda = info.get("currency", "USD")
        precio_anterior = info.get("previousClose", "No disponible")
        
        # Calcular cambio
        cambio_porcentaje = None
        if isinstance(precio_actual, (int, float)) and isinstance(precio_anterior, (int, float)):
            cambio_porcentaje = ((precio_actual - precio_anterior) / precio_anterior) * 100
            
        return {
            "ticker": ticker,
            "nombre": nombre_empresa,
            "precio": precio_actual,
            "moneda": moneda,
            "cierre_anterior": precio_anterior,
            "cambio_porcentaje": cambio_porcentaje,
            "resumen": info.get("longBusinessSummary", "No hay resumen disponible.")
        }
    except Exception as e:
        print(f"Error al obtener datos para {ticker}: {e}")
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
