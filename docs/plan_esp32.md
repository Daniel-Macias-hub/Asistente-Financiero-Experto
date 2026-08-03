# Plan de Integración con ESP32-S3

El software actual se ha desarrollado en Python para demostrar la viabilidad lógica (MVP), la base de conocimientos y el motor de inferencia. Para la etapa final, el sistema será migrado a un ESP32-S3.

## Restricciones del ESP32-S3
- **Memoria RAM:** ~512KB SRAM (más PSRAM externa 2MB-8MB).
- **Procesador:** Xtensa dual-core 32-bit LX7, hasta 240 MHz.
- **Almacenamiento:** Memoria Flash SPI (generalmente 4MB a 16MB).

## Estrategia de Migración

### 1. Base de Conocimientos
- **Actual:** SQLite3 en Python.
- **Migración ESP32:** MicroPython no incluye SQLite por defecto, pero se puede usar un formato de almacenamiento ligero como `JSON` o `B-Tree` almacenado en el sistema de archivos de la Flash (SPIFFS / LittleFS). Alternativamente, se puede compilar una versión ligera de SQLite para ESP-IDF si se programa en C/C++.

### 2. Motor de Inferencia
- **Actual:** Lógica de encadenamiento y expansión semántica en Python.
- **Migración ESP32:** La lógica es pura y de bajo coste computacional (comparación de cadenas y diccionarios). Puede ser portada directamente a MicroPython o C++.

### 3. Procesamiento de Audio (El mayor desafío)
- **STT (Speech to Text):**
  - Vosk no puede correr en un ESP32 (requiere demasiada RAM y CPU).
  - *Solución:* Utilizar el framework **ESP-SR** de Espressif. Permite reconocimiento de palabras clave (Wake Word) y comandos de voz offline locales. El diccionario de comandos será la lista de conceptos y reglas conocidos.
- **TTS (Text to Speech):**
  - pyttsx3 requiere un SO completo.
  - *Solución:* Se puede utilizar un chip externo especializado (ej. TTS chip XFS5152) conectado por UART, o sintetizadores ligeros por software como **Flite** o librerías TTS simples en C optimizadas para el DAC del ESP32.

### 4. Interfaz
- **Actual:** Tkinter (GUI de escritorio).
- **Migración ESP32:** Pantalla LCD/OLED vía I2C/SPI mostrando el historial y estado. Botones físicos para accionar el micrófono y modos.
