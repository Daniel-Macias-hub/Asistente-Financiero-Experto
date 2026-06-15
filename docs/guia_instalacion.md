# Guía de Instalación y Pruebas

## Requisitos Previos
1. Python 3.9 o superior.
2. Micrófono y altavoces configurados en el equipo.

## Instalación

1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Descargar Modelo Vosk (Offline STT):**
   - Ve a la página oficial de modelos Vosk: https://alphacephei.com/vosk/models
   - Descarga el modelo pequeño para español: `vosk-model-small-es-0.42` (o similar).
   - Extrae el archivo ZIP.
   - Renombra la carpeta extraída a `modelo_vosk` y colócala en la raíz del proyecto `d:\INTELIGENCIA_DE_NEGOCIOS\asistente_financiero\modelo_vosk`.

## Ejecución

Para iniciar el Asistente Educativo:
```bash
python main.py
```
La primera vez que se ejecute, el sistema creará el archivo `conocimiento.db` e inyectará los datos base.

## Casos de Uso y Pruebas

### 1. Consulta Básica (Extracción de Conceptos)
- **Usuario ingresa:** "¿Me puedes explicar qué es un ETF y el riesgo?"
- **Resultado esperado:** El motor detecta los conceptos "ETF" y "Riesgo". Retorna la definición de ambos, y muestra que el ETF se relaciona con la Diversificación.

### 2. Inferencia Basada en Reglas
- **Usuario ingresa:** "Quiero reducir mi riesgo, ¿qué hago?"
- **Resultado esperado:** La regla `reducir riesgo` se dispara y recomienda la diversificación. Luego extrae el concepto "riesgo" y da su definición.

### 3. Entrenamiento (Agregar Conocimiento)
1. Ve a la pestaña **Entrenamiento > Conceptos**.
2. **Nombre:** Interés Compuesto
3. **Definición:** Acumulación de intereses sobre el capital principal y los intereses generados previamente.
4. Presiona **Guardar**.
5. Ve a la pestaña **Consulta** y pregunta por el "interés compuesto". El sistema ahora responderá con este nuevo conocimiento.

### 4. Prueba de Voz
1. Haz clic en **🎙️ Consultar Voz**.
2. Habla por el micrófono (ej. "¿Qué es una acción?").
3. Espera un segundo al terminar.
4. El sistema convertirá tu voz a texto, procesará la inferencia y responderá tanto en texto en pantalla como en audio sintetizado.
