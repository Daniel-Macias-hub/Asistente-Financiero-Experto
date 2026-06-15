# Arquitectura del Sistema

El Asistente de Voz Educativo se basa en una arquitectura modular de Sistema Experto Clásico, diseñado para operar en un entorno con recursos restringidos (futura integración con ESP32-S3).

## Diagrama de Bloques

```text
+-------------------+       +-----------------------+       +-------------------+
|                   |       |                       |       |                   |
|  Micrófono (Voz)  | ----> |  Módulo de Audio      | ----> |  Motor de         |
|  Teclado (Texto)  |       |  (STT: Vosk offline)  |       |  Inferencia       |
|                   |       |                       |       |                   |
+-------------------+       +-----------------------+       +---------+---------+
                                                                      |
                                                                      v
+-------------------+       +-----------------------+       +-------------------+
|                   |       |                       |       |                   |
|  Módulo de        | <---- |  Módulo de            | <---- |  Base de          |
|  Entrenamiento    |       |  Conocimiento         |       |  Datos SQLite     |
|                   |       |  (Gestor de DB)       |       |  (Reglas, Hechos) |
+-------------------+       +-----------------------+       +-------------------+
                                                                      |
+-------------------+       +-----------------------+                 |
|                   |       |                       |                 |
|  Altavoz (Voz)    | <---- |  Módulo de Audio      | <---------------+
|  Pantalla (Texto) |       |  (TTS: pyttsx3)       |
|                   |       |                       |
+-------------------+       +-----------------------+
```

## Componentes

1. **Base de Conocimientos (SQLite):**
   - No utiliza grafos pesados ni IA generativa. Utiliza un esquema relacional ligero para almacenar:
     - Conceptos y definiciones.
     - Relaciones direccionales (Ej. ETF -> reduce -> Riesgo).
     - Reglas de inferencia (SI "reducir riesgo" ENTONCES "sugerir diversificación").

2. **Motor de Inferencia:**
   - Implementa encadenamiento hacia adelante (forward chaining).
   - Analiza el texto para disparar reglas.
   - Extrae conceptos y realiza "expansión semántica" al buscar sus relaciones directas para enriquecer la respuesta.

3. **Módulo de Audio:**
   - **STT (Speech-to-Text):** Vosk. Permite reconocimiento continuo de voz en tiempo real sin requerir conexión a internet.
   - **TTS (Text-to-Speech):** pyttsx3. Utiliza los motores de síntesis de voz integrados en el sistema operativo (SAPI5 en Windows, NSSpeechSynthesizer en macOS, espeak en Linux).

4. **Módulo de Entrenamiento:**
   - Capa lógica que permite ingresar nuevos hechos y reglas a la base de datos de manera controlada, garantizando que el sistema "aprenda" sin necesidad de reentrenar modelos matemáticos.
