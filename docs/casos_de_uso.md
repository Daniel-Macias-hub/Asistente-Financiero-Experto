# Casos de Uso y Ejemplos de Interacción

## Caso 1: Consulta Directa por Voz
**Actor:** Usuario
**Precondición:** El micrófono está habilitado y el modelo Vosk está configurado.
1. El usuario presiona "Consultar Voz" en la interfaz.
2. El sistema indica que está escuchando.
3. El usuario dice: "¿Qué es un ETF?"
4. El sistema transcribe el audio, busca "ETF" en la base de datos de conceptos y devuelve la definición.
5. El sistema sintetiza la respuesta con pyttsx3 y la reproduce por el altavoz, a la vez que la muestra en el historial.

## Caso 2: Encadenamiento de Reglas
**Actor:** Usuario
**Precondición:** Existe la regla `(condicion="reducir riesgo", conclusion="diversificacion")`.
1. El usuario escribe: "Necesito reducir mi riesgo al invertir".
2. El sistema detecta la condición "reducir riesgo".
3. El motor de inferencia dispara la conclusión: "Se recomienda emplear la diversificación de activos".
4. Adicionalmente, el sistema extrae la palabra "riesgo", devuelve su definición y muestra su relación con "diversificación".

## Caso 3: Entrenamiento del Sistema (Aprender nuevo concepto)
**Actor:** Usuario / Administrador
1. El usuario ingresa a la pestaña "Entrenamiento" y selecciona "Conceptos".
2. Escribe el Nombre del concepto: "Bono".
3. Escribe la definición: "Instrumento de deuda de renta fija."
4. Presiona Guardar.
5. El sistema inserta en la base de datos SQLite y confirma.
6. El usuario pregunta por "Bono" en la pestaña "Consulta" y el sistema responde adecuadamente.
