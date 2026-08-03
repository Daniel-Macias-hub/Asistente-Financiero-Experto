import yfinance as yf
from api_financiera.coingecko import obtener_info_cripto

CRYPTO_TICKER_MAP = {
    "BTC": "bitcoin",
    "BITCOIN": "bitcoin",
    "ETH": "ethereum",
    "ETHEREUM": "ethereum",
    "SOL": "solana",
    "SOLANA": "solana",
    "ADA": "cardano",
    "CARDANO": "cardano",
    "XRP": "ripple",
    "DOGE": "dogecoin",
    "DOGECOIN": "dogecoin",
    "BNB": "binancecoin"
}

CRYPTO_DETAILS = {
    "BITCOIN": {
        "simbolo": "BTC",
        "nombre": "Bitcoin",
        "anio_creacion": "2009 (Creado por Satoshi Nakamoto)",
        "precio_inicial": "$0.0008 USD en 2009",
        "exchanges": "Bitso, Binance, Coinbase, Kraken",
        "descripcion": "Primera criptomoneda descentralizada del mundo basada en Proof of Work con límite de 21 millones de monedas."
    },
    "ETHEREUM": {
        "simbolo": "ETH",
        "nombre": "Ethereum",
        "anio_creacion": "2015 (Creado por Vitalik Buterin)",
        "precio_inicial": "$0.31 USD en su ICO de 2014",
        "exchanges": "Bitso, Binance, Coinbase, Uniswap",
        "descripcion": "Plataforma líder para contratos inteligentes (Smart Contracts) y aplicaciones descentralizadas (dApps)."
    },
    "DOGECOIN": {
        "simbolo": "DOGE",
        "nombre": "Dogecoin",
        "anio_creacion": "2013 (Creado por Billy Markus y Jackson Palmer)",
        "precio_inicial": "$0.00026 USD en 2013",
        "exchanges": "Bitso, Binance, Coinbase, Robinhood",
        "descripcion": "Memecoin popular basada en el perro Shiba Inu, optimizada para pagos rápidos de ultra bajo costo."
    },
    "SOLANA": {
        "simbolo": "SOL",
        "nombre": "Solana",
        "anio_creacion": "2020 (Creado por Anatoly Yakovenko)",
        "precio_inicial": "$0.22 USD en 2020",
        "exchanges": "Bitso, Binance, Coinbase, Raydium",
        "descripcion": "Blockchain de ultra alta velocidad (Proof of History) capaz de procesar +50,000 transacciones por segundo."
    },
    "CARDANO": {
        "simbolo": "ADA",
        "nombre": "Cardano",
        "anio_creacion": "2017 (Creado por Charles Hoskinson)",
        "precio_inicial": "$0.0024 USD en 2017",
        "exchanges": "Bitso, Binance, Coinbase",
        "descripcion": "Blockchain de tercera generación revisada por pares científicos orientada a seguridad y sostenibilidad."
    },
    "XRP": {
        "simbolo": "XRP",
        "nombre": "Ripple XRP",
        "anio_creacion": "2012 (Creado por Jed McCaleb y Chris Larsen)",
        "precio_inicial": "$0.005 USD en 2012",
        "exchanges": "Bitso, Binance, KuCoin",
        "descripcion": "Diseñada para liquidaciones financieras internacionales e interbancarias en segundos."
    },
    "BNB": {
        "simbolo": "BNB",
        "nombre": "Binance Coin",
        "anio_creacion": "2017 (Creado por Changpeng Zhao)",
        "precio_inicial": "$0.10 USD en su ICO de 2017",
        "exchanges": "Binance, PancakeSwap",
        "descripcion": "Criptomoneda nativa del ecosistema global Binance y la red BNB Chain."
    }
}

TASA_CAMBIO_MXN = 20.0  # Tasa de cambio promedio USD -> MXN

def obtener_datos_accion(ticker: str) -> dict:
    """
    Obtiene información completa y didáctica de mercado en USD y MXN.
    """
    ticker_clean = ticker.strip().upper()
    info_extra = CRYPTO_DETAILS.get(ticker_clean, {})
    if not info_extra:
        for k, v in CRYPTO_DETAILS.items():
            if v.get("simbolo") == ticker_clean or k == ticker_clean:
                info_extra = v
                break


    # 1. Si es Criptomoneda, consultar CoinGecko primero
    try:
        cg_id = CRYPTO_TICKER_MAP.get(ticker_clean, ticker_clean.lower())
        info_cg = obtener_info_cripto(cg_id)
        if info_cg and info_cg.get("precio_usd", 0) > 0:
            p_usd = info_cg.get("precio_usd", 0.0)
            # Usar precio MXN de CoinGecko si está disponible (más preciso que tasa fija)
            p_mxn = info_cg.get("precio_mxn", 0.0) or (p_usd * TASA_CAMBIO_MXN)
            return {
                "ticker": info_cg.get("simbolo", info_extra.get("simbolo", ticker_clean)),
                "nombre": info_cg.get("nombre", info_extra.get("nombre", ticker_clean)),
                "precio": p_usd,
                "precio_mxn": p_mxn,
                "moneda": "USD",
                "cambio_porcentaje": info_cg.get("cambio_24h"),
                "anio_creacion": info_extra.get("anio_creacion", "Información en base de conocimiento"),
                "precio_inicial": info_extra.get("precio_inicial", "N/A"),
                "exchanges": info_extra.get("exchanges", "Bitso, Binance, Coinbase"),
                "resumen": info_extra.get("descripcion", f"Criptomoneda {ticker_clean} en tiempo real.")
            }
    except Exception:
        pass

    # 2. Si es una Acción o Fallback
    yf_ticker = ticker_clean if "-" in ticker_clean else f"{ticker_clean}-USD"
    try:
        accion = yf.Ticker(yf_ticker)
        info = accion.info
        if info and ("currentPrice" in info or "regularMarketPrice" in info):
            precio_actual = info.get("currentPrice") or info.get("regularMarketPrice")
            p_mxn = precio_actual * TASA_CAMBIO_MXN
            # Calcular % de cambio correctamente (previousClose es un precio, no un %)
            prev_close = info.get("previousClose")
            cambio_pct = None
            if prev_close and prev_close > 0:
                cambio_pct = ((precio_actual - prev_close) / prev_close) * 100
            return {
                "ticker": ticker_clean,
                "nombre": info.get("shortName") or info.get("longName", ticker_clean),
                "precio": precio_actual,
                "precio_mxn": p_mxn,
                "moneda": "USD",
                "cambio_porcentaje": cambio_pct,
                "anio_creacion": "Mercado bursátil global",
                "precio_inicial": "N/A",
                "exchanges": "Bolsa de Valores, Broker regulado",
                "resumen": info.get("longBusinessSummary", "Sin resumen disponible.")
            }
    except Exception:
        pass

    # 3. Fallback honesto: ambas APIs fallaron, no mostrar precios inventados
    return {
        "ticker": info_extra.get("simbolo", ticker_clean),
        "nombre": info_extra.get("nombre", ticker_clean),
        "precio": 0.0,
        "precio_mxn": 0.0,
        "moneda": "USD",
        "cambio_porcentaje": None,
        "anio_creacion": info_extra.get("anio_creacion", "N/A"),
        "precio_inicial": info_extra.get("precio_inicial", "N/A"),
        "exchanges": info_extra.get("exchanges", "Bitso, Binance"),
        "resumen": "⚠️ No se pudo obtener el precio en tiempo real. Verifica tu conexión a Internet."
    }

def generar_sintesis_hablada(ticker: str) -> str:
    """
    Genera un texto conversacional fluido y didáctico para la síntesis de voz (TTS),
    explicando precio USD/MXN, año de creación, dónde comprar y resumen.
    """
    datos = obtener_datos_accion(ticker)
    if not datos:
        return f"No se encontraron datos para {ticker}."
    
    nombre = datos.get("nombre", ticker)
    p_usd = datos.get("precio", 0.0)
    p_mxn = datos.get("precio_mxn", 0.0)
    anio = datos.get("anio_creacion", "")
    p_ini = datos.get("precio_inicial", "")
    exchanges = datos.get("exchanges", "")
    resumen = datos.get("resumen", "")

    sintesis = (
        f"Criptomoneda identificada: {nombre}. "
        f"Su precio actual es de {p_usd:,.2f} dólares, equivalentes a {p_mxn:,.2f} pesos mexicanos. "
        f"Origen y año de creación: {anio}. Su precio inicial histórico fue {p_ini}. "
        f"Puedes adquirirla en plataformas como {exchanges}. "
        f"En resumen: {resumen}"
    )
    return sintesis

def generar_respuesta_precio(ticker: str) -> tuple[str, list]:
    datos = obtener_datos_accion(ticker)
    logs = [f"Consulta realizada para {ticker}"]
    
    if datos and "precio" in datos:
        cambio_str = ""
        if datos.get("cambio_porcentaje") is not None:
            pct = datos["cambio_porcentaje"]
            signo = "+" if pct >= 0 else ""
            cambio_str = f" ({signo}{pct:.2f}% en 24h)"
            
        res = (
            f"📊 **ANÁLISIS DE MERCADO EN TIEMPO REAL: {datos['nombre'].upper()} ({datos['ticker']})**\n"
            f"──────────────────────────────────────────────────────────\n"
            f"💰 **Precio Actual USD:** ${datos['precio']:,.2f} USD{cambio_str}\n"
            f"🇲🇽 **Precio Estimado MXN:** ${datos['precio_mxn']:,.2f} Pesos Mexicanos\n"
            f"📅 **Año de Creación:** {datos.get('anio_creacion')}\n"
            f"💵 **Precio Inicial Histórico:** {datos.get('precio_inicial')}\n"
            f"🏦 **Dónde Comprar en México / Global:** {datos.get('exchanges')}\n"
            f"📖 **Resumen Didáctico:** {datos.get('resumen')}"
        )
        return res, logs
    else:
        return f"Lo siento, no pude obtener los datos de mercado para '{ticker}'.", logs


# Alias de compatibilidad
obtener_datos_cripto = obtener_datos_accion

