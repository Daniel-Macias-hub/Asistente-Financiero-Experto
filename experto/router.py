"""
Router de intención para el motor experto.
Clasifica la consulta del usuario para determinar si debe ser atendida por:
- La base de conocimientos local (offline)
- Las APIs financieras (online)
- El módulo de visión (cámara)
"""
from config import CRYPTO_MAP


# Palabras clave que indican intención de consulta de precios
KEYWORDS_PRECIO = [
    "precio", "vale", "cuesta", "cotiza", "cotización", "valor actual",
    "cuanto cuesta", "cuanto vale", "a cuanto esta", "a como esta",
    "precio actual", "precio de", "cuánto vale", "cuánto cuesta",
]

# Palabras clave que indican intención de consulta de mercado general
KEYWORDS_MERCADO = [
    "mercado", "top criptos", "ranking", "mejores criptomonedas",
    "como va el mercado", "estado del mercado", "resumen del mercado",
    "criptomonedas hoy", "mercado hoy",
]

# Nombres de criptomonedas y sus sinónimos comunes
NOMBRES_CRIPTO = set(CRYPTO_MAP.keys())
SINONIMOS_CRIPTO = {
    "btc": "bitcoin", "eth": "ethereum", "sol": "solana",
    "ada": "cardano", "doge": "dogecoin", "dot": "polkadot",
    "ltc": "litecoin", "trx": "tron", "link": "chainlink",
    "avax": "avalanche", "ripple": "xrp",
}


def clasificar_intencion(texto):
    """
    Clasifica la intención de la consulta del usuario.
    
    Args:
        texto: Texto normalizado del usuario.
    
    Returns:
        tuple (tipo_intencion, cripto_detectada)
        tipo_intencion: "precio" | "mercado" | "concepto"
        cripto_detectada: nombre de la cripto si se detectó, None si no.
    """
    texto_lower = texto.lower()
    
    # 1. Detectar si menciona una criptomoneda
    cripto = _detectar_criptomoneda(texto_lower)
    
    # 2. Verificar si pide precio
    es_precio = any(kw in texto_lower for kw in KEYWORDS_PRECIO)
    
    # 3. Verificar si pide mercado general
    es_mercado = any(kw in texto_lower for kw in KEYWORDS_MERCADO)
    
    if es_mercado and not cripto:
        return "mercado", None
    
    if es_precio and cripto:
        return "precio", cripto
    
    # Si menciona una cripto sin pedir precio explícitamente,
    # puede ser que quiera información general o definición
    if cripto:
        # Si el texto parece una pregunta de concepto ("qué es"), ir a la base local
        if "que es" in texto_lower or "qué es" in texto_lower or "definicion" in texto_lower:
            return "concepto", cripto
        # Por defecto, si menciona una cripto, asumir que quiere precio
        return "precio", cripto
    
    # Default: ir a base de conocimiento local
    return "concepto", None


def _detectar_criptomoneda(texto):
    """
    Detecta si el texto menciona alguna criptomoneda conocida.
    
    Returns:
        Nombre normalizado de la cripto, o None.
    """
    # Buscar nombres directos
    for nombre in NOMBRES_CRIPTO:
        if nombre in texto:
            return nombre
    
    # Buscar sinónimos
    for sinonimo, nombre in SINONIMOS_CRIPTO.items():
        # Usar búsqueda de palabras completas para evitar falsos positivos
        palabras = texto.split()
        if sinonimo in palabras:
            return nombre
    
    return None
