import re
import unicodedata
from conocimiento.database import get_connection

def quitar_acentos(texto):
    """Elimina tildes y caracteres especiales para normalizar el texto."""
    texto = unicodedata.normalize('NFD', texto)
    texto = texto.encode('ascii', 'ignore').decode('utf-8')
    return texto

def normalizar_texto(texto):
    """
    Normaliza el texto de entrada.
    1. Convierte a minúsculas.
    2. Elimina acentos.
    3. Reemplaza alias y traducciones fonéticas por el concepto real (basado en SQLite).
    """
    texto = texto.lower()
    texto = quitar_acentos(texto)
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT sinonimo, termino FROM sinonimos")
    resultados = cursor.fetchall()
    conn.close()
    
    # Ordenamos por longitud del sinónimo descendente para evitar que 
    # un sinónimo corto reemplace parte de un sinónimo más largo.
    reemplazos = sorted(resultados, key=lambda x: len(x['sinonimo']), reverse=True)
    
    for row in reemplazos:
        # Quitamos acentos también a los sinónimos de la BD por seguridad
        sinonimo_norm = quitar_acentos(row['sinonimo'].lower())
        termino_norm = row['termino'].lower() # El término base no necesita quitar acentos para la BD, pero lo dejamos como está en BD
        
        # Reemplazo de palabras completas usando expresiones regulares
        # \b asegura que solo reemplacemos la palabra exacta y no partes de palabras
        patron = r'\b' + re.escape(sinonimo_norm) + r'\b'
        texto = re.sub(patron, termino_norm, texto)
        
    return texto
