import re
import unicodedata
from conocimiento.database import get_connection

def quitar_acentos(texto):
    """Elimina tildes y caracteres especiales para normalizar el texto."""
    texto = unicodedata.normalize('NFD', texto)
    texto = texto.encode('ascii', 'ignore').decode('utf-8')
    return texto

# Caché de sinónimos en memoria — se carga una vez y se reutiliza
_CACHE_SINONIMOS = None

def _obtener_sinonimos():
    """Carga sinónimos desde BD solo la primera vez; luego usa la caché en memoria."""
    global _CACHE_SINONIMOS
    if _CACHE_SINONIMOS is None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT sinonimo, termino FROM sinonimos")
        resultados = cursor.fetchall()
        conn.close()
        # Ordenar por longitud descendente para evitar reemplazos parciales
        _CACHE_SINONIMOS = sorted(resultados, key=lambda x: len(x['sinonimo']), reverse=True)
    return _CACHE_SINONIMOS

def invalidar_cache_sinonimos():
    """Llama a esta función si se agregan nuevos sinónimos en runtime."""
    global _CACHE_SINONIMOS
    _CACHE_SINONIMOS = None

def normalizar_texto(texto):
    """
    Normaliza el texto de entrada.
    1. Convierte a minúsculas.
    2. Elimina acentos.
    3. Reemplaza alias y traducciones fonéticas por el concepto real (basado en SQLite).
    """
    texto = texto.lower()
    texto = quitar_acentos(texto)
    # Eliminar signos de puntuación (conservar solo alfanuméricos y espacios)
    texto = re.sub(r'[^\w\s]', '', texto)

    for row in _obtener_sinonimos():
        # Quitar acentos también a los sinónimos por seguridad
        sinonimo_norm = quitar_acentos(row['sinonimo'].lower())
        termino_norm = row['termino'].lower()
        # Reemplazo de palabras completas usando expresiones regulares
        patron = r'\b' + re.escape(sinonimo_norm) + r'\b'
        texto = re.sub(patron, termino_norm, texto)

    return texto
