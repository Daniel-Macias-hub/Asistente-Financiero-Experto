from .database import get_connection

def obtener_todas_las_reglas():
    """Obtiene todas las reglas de inferencia de la base de datos."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT condicion, conclusion FROM reglas")
    resultados = cursor.fetchall()
    conn.close()
    return [{"condicion": r["condicion"], "conclusion": r["conclusion"]} for r in resultados]

def obtener_reglas_por_condicion(palabra_clave):
    """Busca reglas que contengan una palabra clave en su condición."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT condicion, conclusion FROM reglas WHERE condicion LIKE ?", (f"%{palabra_clave}%",))
    resultados = cursor.fetchall()
    conn.close()
    return [{"condicion": r["condicion"], "conclusion": r["conclusion"]} for r in resultados]
