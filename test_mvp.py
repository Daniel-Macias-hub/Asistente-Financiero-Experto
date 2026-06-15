import os
import sqlite3
from conocimiento.database import inicializar_db, DB_PATH
from entrenamiento.agregar_concepto import nuevo_concepto
from entrenamiento.agregar_relacion import nueva_relacion
from entrenamiento.agregar_regla import nueva_regla
from experto.motor import procesar_consulta
from audio.tts import hablar

def ejecutar_pruebas():
    print("=== INICIANDO PRUEBAS FUNCIONALES DEL MVP ===")
    
    # 3. Crear BD si no existe
    print("\n[Paso 3] Inicializando Base de Datos...")
    inicializar_db()
    if os.path.exists(DB_PATH):
        print("✓ Base de datos creada/verificada exitosamente.")
    else:
        print("✗ Error al crear base de datos.")

    # 4. Insertar Concepto
    print("\n[Paso 4] Insertando concepto 'ETF'...")
    exito, msj = nuevo_concepto("ETF", "Fondo cotizado que replica un índice.")
    print(f"Resultado: {msj}")
    
    # 5. Consultar Concepto
    print("\n[Paso 5] Consultando: '¿Qué es un ETF?'")
    resp, log = procesar_consulta("¿Qué es un ETF?")
    print("Logs del Motor:")
    for l in log: print(f"  - {l}")
    print(f"Respuesta del Sistema:\n{resp}")

    # 6. Insertar Relación
    print("\n[Paso 6] Insertando relación: ETF -> diversificación")
    # Para poder relacionar, el destino debe existir. Insertamos 'diversificación' primero.
    nuevo_concepto("diversificación", "Estrategia para reducir el riesgo.")
    exito, msj = nueva_relacion("ETF", "diversificación", "permite")
    print(f"Resultado: {msj}")

    # 7. Insertar Regla
    print("\n[Paso 7] Insertando regla: riesgo -> diversificación")
    # Condicion: "reducir riesgo", Conclusion: "emplear la diversificación de activos"
    exito, msj = nueva_regla("reducir riesgo", "Se recomienda emplear la diversificación de activos")
    print(f"Resultado: {msj}")

    # 8. Consultar Inferencia
    print("\n[Paso 8] Consultando: '¿Cómo puedo reducir el riesgo?'")
    resp, log = procesar_consulta("¿Cómo puedo reducir el riesgo?")
    print("Logs del Motor:")
    for l in log: print(f"  - {l}")
    print(f"Respuesta del Sistema:\n{resp}")

    # 9. Mostrar Tablas SQLite
    print("\n[Paso 9] Contenido de tablas SQLite:")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, definicion FROM conceptos")
    print("CONCEPTOS:", cursor.fetchall())
    cursor.execute("SELECT origen, destino, tipo_relacion FROM relaciones")
    print("RELACIONES:", cursor.fetchall())
    cursor.execute("SELECT condicion, conclusion FROM reglas")
    print("REGLAS:", cursor.fetchall())
    conn.close()

    # 10. Probar TTS
    print("\n[Paso 10] Probando Audio (pyttsx3)... Escucha los altavoces.")
    try:
        hablar("Prueba de audio completada.")
        print("✓ Audio reproducido correctamente.")
    except Exception as e:
        print(f"✗ Error reproduciendo audio: {e}")

    # 11. Probar Vosk
    print("\n[Paso 11] Probando modelo Vosk (Validación de carga)...")
    from audio.stt import MODEL_DIR
    if os.path.exists(MODEL_DIR):
        print(f"✓ La carpeta del modelo Vosk existe en: {MODEL_DIR}")
    else:
        print(f"✗ ¡Modelo Vosk NO encontrado! Debes descargarlo en {MODEL_DIR}")

    print("\n=== PRUEBAS FUNCIONALES FINALIZADAS ===")

if __name__ == "__main__":
    ejecutar_pruebas()
