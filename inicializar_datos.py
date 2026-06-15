from conocimiento.database import get_connection
import sqlite3

def pre_cargar_conocimiento():
    """Inyecta datos iniciales a la base de conocimientos para demostración."""
    conn = get_connection()
    cursor = conn.cursor()
    
    conceptos = [
        ("accion", "Parte alícuota del capital social de una sociedad anónima."),
        ("etf", "Exchange Traded Fund. Fondo de inversión que cotiza en bolsa como si fuera una acción."),
        ("riesgo", "Probabilidad de que una inversión produzca un retorno menor al esperado o pierda valor."),
        ("diversificacion", "Estrategia de inversión que consiste en distribuir el capital en distintos activos para reducir el riesgo global."),
        ("s&p 500", "Índice bursátil que representa a las 500 empresas más grandes de Estados Unidos."),
        ("nasdaq", "Índice bursátil que agrupa a las principales empresas tecnológicas."),
        ("renta fija", "Inversiones donde se conoce de antemano el interés a recibir, como los bonos."),
        ("renta variable", "Inversiones donde no se conoce la rentabilidad futura, como las acciones.")
    ]
    
    relaciones = [
        ("etf", "diversificacion", "permite"),
        ("diversificacion", "riesgo", "reduce"),
        ("s&p 500", "renta variable", "es un tipo de"),
        ("accion", "renta variable", "es un tipo de")
    ]
    
    reglas = [
        ("reducir riesgo", "Se recomienda emplear la diversificación de activos"),
        ("que es etf", "Un ETF es una excelente forma de diversificar"),
        ("invertir tecnologia", "El índice NASDAQ agrupa a las principales empresas tecnológicas")
    ]
    
    sinonimos = [
        ("accion", "acciones"),
        ("etf", "etfs"),
        ("etf", "e te efe"),
        ("etf", "eiti efe"),
        ("etf", "fondo indexado"),
        ("etf", "fondo cotizado"),
        ("s&p 500", "ese y pe quinientos"),
        ("nasdaq", "nas dac"),
        ("riesgo", "riesgos"),
        ("diversificacion", "diversificar")
    ]
    
    preguntas_frecuentes = [
        ("quien eres", "Soy un asistente experto en educación financiera diseñado sin IA comercial, operando 100% offline."),
        ("como funcionas", "Funciono a través de un motor de inferencia basado en reglas y una base de conocimientos local en SQLite.")
    ]
    
    for c in conceptos:
        try: cursor.execute("INSERT INTO conceptos (nombre, definicion) VALUES (?, ?)", c)
        except sqlite3.IntegrityError: pass
        
    for r in relaciones:
        try: cursor.execute("INSERT INTO relaciones (origen, destino, tipo_relacion) VALUES (?, ?, ?)", r)
        except sqlite3.IntegrityError: pass
        
    for reg in reglas:
        try: cursor.execute("INSERT INTO reglas (condicion, conclusion) VALUES (?, ?)", reg)
        except sqlite3.IntegrityError: pass
        
    for s in sinonimos:
        try: cursor.execute("INSERT INTO sinonimos (termino, sinonimo) VALUES (?, ?)", s)
        except sqlite3.IntegrityError: pass
        
    for p in preguntas_frecuentes:
        try: cursor.execute("INSERT INTO preguntas_frecuentes (pregunta, respuesta) VALUES (?, ?)", p)
        except sqlite3.IntegrityError: pass
        
    conn.commit()
    conn.close()
    print("Conocimiento inicial pre-cargado exitosamente.")

if __name__ == "__main__":
    from conocimiento.database import inicializar_db
    inicializar_db()
    pre_cargar_conocimiento()
