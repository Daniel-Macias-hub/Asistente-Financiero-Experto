"""
Sistema de caché local para datos de APIs financieras.
Almacena precios y datos de mercado en SQLite con TTL configurable.
Permite funcionamiento degradado cuando no hay Internet.
"""
import time
from conocimiento.database import get_connection
from config import CACHE_TTL_SECONDS


def inicializar_tabla_cache():
    """Crea la tabla de caché si no existe."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cache_precios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cripto_nombre TEXT NOT NULL,
        precio_usd REAL DEFAULT 0,
        precio_mxn REAL DEFAULT 0,
        market_cap REAL DEFAULT 0,
        volumen_24h REAL DEFAULT 0,
        cambio_24h REAL DEFAULT 0,
        ranking INTEGER DEFAULT 0,
        timestamp REAL NOT NULL,
        UNIQUE(cripto_nombre)
    )
    ''')
    conn.commit()
    conn.close()


def guardar_en_cache(nombre, datos):
    """
    Guarda o actualiza datos de una criptomoneda en el caché.
    
    Args:
        nombre: Nombre de la criptomoneda.
        datos: dict con precio_usd, precio_mxn, market_cap, volumen_24h, cambio_24h, ranking.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO cache_precios (cripto_nombre, precio_usd, precio_mxn, market_cap, volumen_24h, cambio_24h, ranking, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(cripto_nombre) DO UPDATE SET
        precio_usd = excluded.precio_usd,
        precio_mxn = excluded.precio_mxn,
        market_cap = excluded.market_cap,
        volumen_24h = excluded.volumen_24h,
        cambio_24h = excluded.cambio_24h,
        ranking = excluded.ranking,
        timestamp = excluded.timestamp
    ''', (
        nombre.lower(),
        datos.get("precio_usd", 0),
        datos.get("precio_mxn", 0),
        datos.get("market_cap", 0),
        datos.get("volumen_24h", 0),
        datos.get("cambio_24h", 0),
        datos.get("ranking", 0),
        time.time()
    ))
    
    conn.commit()
    conn.close()


def obtener_de_cache(nombre):
    """
    Obtiene datos de una criptomoneda desde el caché local.
    Solo retorna datos si no han expirado (TTL).
    
    Args:
        nombre: Nombre de la criptomoneda.
    
    Returns:
        dict con los datos cacheados, o None si no existe o expiró.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM cache_precios WHERE cripto_nombre = ?", 
        (nombre.lower(),)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        return None
    
    # Verificar TTL
    edad = time.time() - row["timestamp"]
    if edad > CACHE_TTL_SECONDS:
        return None  # Caché expirado
    
    return {
        "precio_usd": row["precio_usd"],
        "precio_mxn": row["precio_mxn"],
        "market_cap": row["market_cap"],
        "volumen_24h": row["volumen_24h"],
        "cambio_24h": row["cambio_24h"],
        "ranking": row["ranking"],
        "desde_cache": True,
        "edad_segundos": edad,
    }


def obtener_de_cache_sin_ttl(nombre):
    """
    Obtiene datos del caché ignorando el TTL.
    Útil como fallback cuando no hay Internet.
    
    Args:
        nombre: Nombre de la criptomoneda.
    
    Returns:
        dict con los datos cacheados (pueden ser antiguos), o None.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM cache_precios WHERE cripto_nombre = ?", 
        (nombre.lower(),)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        return None
    
    return {
        "precio_usd": row["precio_usd"],
        "precio_mxn": row["precio_mxn"],
        "market_cap": row["market_cap"],
        "volumen_24h": row["volumen_24h"],
        "cambio_24h": row["cambio_24h"],
        "ranking": row["ranking"],
        "desde_cache": True,
        "edad_segundos": time.time() - row["timestamp"],
    }


def obtener_todo_cache():
    """
    Retorna todos los datos del caché (para el dashboard).
    
    Returns:
        Lista de dicts ordenados por ranking.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM cache_precios ORDER BY ranking ASC")
    rows = cursor.fetchall()
    conn.close()
    
    return [{
        "nombre": row["cripto_nombre"],
        "precio_usd": row["precio_usd"],
        "precio_mxn": row["precio_mxn"],
        "market_cap": row["market_cap"],
        "volumen_24h": row["volumen_24h"],
        "cambio_24h": row["cambio_24h"],
        "ranking": row["ranking"],
        "edad_segundos": time.time() - row["timestamp"],
    } for row in rows]
