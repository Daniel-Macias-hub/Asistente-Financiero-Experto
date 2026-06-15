from .database import get_connection

def obtener_concepto(nombre):
    """Busca un concepto por su nombre exacto o sinónimo."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Buscar como concepto directo
    cursor.execute("SELECT definicion FROM conceptos WHERE nombre LIKE ?", (nombre,))
    row = cursor.fetchone()
    
    if row:
        conn.close()
        return row['definicion']
        
    # Buscar como sinónimo
    cursor.execute("SELECT termino FROM sinonimos WHERE sinonimo LIKE ?", (nombre,))
    sin_row = cursor.fetchone()
    
    if sin_row:
        termino_real = sin_row['termino']
        cursor.execute("SELECT definicion FROM conceptos WHERE nombre = ?", (termino_real,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return row['definicion']
            
    conn.close()
    return None

def buscar_conceptos_clave(texto):
    """Busca conceptos conocidos dentro de un texto dado."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT nombre FROM conceptos")
    conceptos = [row['nombre'].lower() for row in cursor.fetchall()]
    
    cursor.execute("SELECT sinonimo, termino FROM sinonimos")
    sinonimos = {row['sinonimo'].lower(): row['termino'].lower() for row in cursor.fetchall()}
    
    conn.close()
    
    texto_lower = texto.lower()
    encontrados = set()
    
    for concepto in conceptos:
        if concepto in texto_lower:
            encontrados.add(concepto)
            
    for sinonimo, termino in sinonimos.items():
        if sinonimo in texto_lower:
            encontrados.add(termino)
            
    return list(encontrados)
