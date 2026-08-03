from conocimiento.database import get_connection
import sqlite3

def nueva_regla(condicion, conclusion):
    """
    Agrega una regla de inferencia.
    Ejemplo:
    condicion: "reducir riesgo"
    conclusion: "recomendar diversificacion"
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO reglas (condicion, conclusion) VALUES (?, ?)",
            (condicion.lower(), conclusion)
        )
        conn.commit()
        exito = True
        mensaje = "Regla agregada exitosamente."
    except sqlite3.IntegrityError:
        exito = False
        mensaje = "Error: Esta regla ya existe."
    finally:
        conn.close()
    return exito, mensaje
