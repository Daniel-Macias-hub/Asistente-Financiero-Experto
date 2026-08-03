from conocimiento.database import get_connection

def buscar_pregunta_frecuente(texto_usuario):
    """Busca si la consulta coincide con una pregunta frecuente almacenada."""
    conn = get_connection()
    cursor = conn.cursor()
    # Búsqueda usando LIKE para flexibilizar un poco
    cursor.execute("SELECT respuesta FROM preguntas_frecuentes WHERE pregunta LIKE ?", (f"%{texto_usuario}%",))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row['respuesta']
    return None
