from .database import get_connection

def obtener_relaciones(origen):
    """Obtiene las relaciones de un concepto hacia otros."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT destino, tipo_relacion FROM relaciones WHERE origen LIKE ?", (origen,))
    resultados = cursor.fetchall()
    conn.close()
    return [{"destino": r["destino"], "tipo_relacion": r["tipo_relacion"]} for r in resultados]

def obtener_relacion_inversa(destino):
    """Obtiene conceptos que apuntan a un destino específico."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT origen, tipo_relacion FROM relaciones WHERE destino LIKE ?", (destino,))
    resultados = cursor.fetchall()
    conn.close()
    return [{"origen": r["origen"], "tipo_relacion": r["tipo_relacion"]} for r in resultados]
