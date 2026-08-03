from conocimiento.database import get_connection
import sqlite3

def nuevo_concepto(nombre, definicion):
    """Agrega un nuevo concepto a la base de conocimientos."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO conceptos (nombre, definicion) VALUES (?, ?)", (nombre.lower(), definicion))
        conn.commit()
        exito = True
        mensaje = f"Concepto '{nombre}' agregado exitosamente."
    except sqlite3.IntegrityError:
        exito = False
        mensaje = f"Error: El concepto '{nombre}' ya existe."
    finally:
        conn.close()
    return exito, mensaje

def nuevo_sinonimo(termino, sinonimo):
    """Agrega un sinónimo asociado a un concepto existente."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO sinonimos (termino, sinonimo) VALUES (?, ?)", (termino.lower(), sinonimo.lower()))
        conn.commit()
        exito = True
        mensaje = f"Sinónimo '{sinonimo}' agregado para el término '{termino}'."
    except sqlite3.IntegrityError:
        exito = False
        mensaje = f"Error: El sinónimo ya existe."
    finally:
        conn.close()
    return exito, mensaje
