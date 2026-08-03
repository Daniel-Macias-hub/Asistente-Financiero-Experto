import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "conocimiento.db")

def get_connection():
    """Devuelve una conexión a la base de datos SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_db():
    """Crea las tablas necesarias si no existen."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabla CONCEPTOS
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS conceptos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        definicion TEXT NOT NULL
    )
    ''')
    
    # Tabla RELACIONES
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS relaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        origen TEXT NOT NULL,
        destino TEXT NOT NULL,
        tipo_relacion TEXT NOT NULL,
        FOREIGN KEY(origen) REFERENCES conceptos(nombre),
        FOREIGN KEY(destino) REFERENCES conceptos(nombre),
        UNIQUE(origen, destino, tipo_relacion)
    )
    ''')
    
    # Tabla REGLAS
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reglas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        condicion TEXT NOT NULL,
        conclusion TEXT NOT NULL,
        UNIQUE(condicion, conclusion)
    )
    ''')
    
    # Tabla SINONIMOS
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sinonimos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        termino TEXT NOT NULL,
        sinonimo TEXT NOT NULL,
        UNIQUE(termino, sinonimo)
    )
    ''')
    
    # Tabla PREGUNTAS_FRECUENTES
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS preguntas_frecuentes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pregunta TEXT UNIQUE NOT NULL,
        respuesta TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    inicializar_db()
    print("Base de datos inicializada correctamente.")
