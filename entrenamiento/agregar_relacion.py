from conocimiento.database import get_connection
import sqlite3

def nueva_relacion(origen, destino, tipo_relacion):
    """
    Agrega una relación semántica entre dos conceptos.
    Ejemplo: origen="etf", destino="diversificación", tipo_relacion="permite"
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO relaciones (origen, destino, tipo_relacion) VALUES (?, ?, ?)",
            (origen.lower(), destino.lower(), tipo_relacion.lower())
        )
        conn.commit()
        exito = True
        mensaje = f"Relación agregada: {origen} -> {tipo_relacion} -> {destino}"
    except sqlite3.IntegrityError:
        exito = False
        mensaje = "Error: Esta relación ya existe o alguno de los conceptos no está registrado."
    finally:
        conn.close()
    return exito, mensaje
