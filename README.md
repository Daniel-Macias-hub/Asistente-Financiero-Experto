# Asistente Financiero Experto (Offline)

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Thonny](https://img.shields.io/badge/IDE-Thonny-green.svg)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)
![Status](https://img.shields.io/badge/Status-MVP-orange.svg)

Un asistente de voz educativo operando 100% **offline**, especializado en educación financiera y bolsa de valores. El sistema utiliza un **Sistema Experto basado en reglas y encadenamiento hacia adelante**, con una base de conocimientos en SQLite (sin depender de IA comercial, LLMs, ni internet). 

El proyecto fue diseñado como prueba de concepto para una futura integración física con el microcontrolador **ESP32-S3**.

## Características Principales
* **100% Local y Offline**: Privacidad total y nula dependencia de APIs.
* **Sistema Experto**: Motor de inferencia propio basado en sentencias y reglas (Forward Chaining).
* **Expansión Semántica**: Asocia conceptos para dar respuestas ricas (Ej. Riesgo -> Diversificación -> ETF).
* **Normalizador Fonético**: Convierte texto como "e te efe" o "nas dac" en los conceptos correctos ("etf", "nasdaq") para mejorar el reconocimiento de voz.
* **Interfaz Gráfica Oscura**: UI moderna ("Dark Mode") construida en Tkinter.
* **Entrenamiento Dinámico**: Permite agregar Conceptos, Relaciones Semánticas y Reglas en tiempo real a través de la interfaz.

---

## Instalación y Ejecución con Thonny IDE

El proyecto está optimizado para funcionar y ejecutarse bajo **Thonny IDE**, un entorno excelente para el aprendizaje y para futuras conexiones con hardware (ESP32).

### 1. Descargar Thonny
Descarga e instala la versión más reciente de Thonny desde su sitio web oficial:
👉 **[https://thonny.org/](https://thonny.org/)**

### 2. Instalar Herramientas dentro de Thonny
Una vez que hayas abierto Thonny, necesitas instalar las librerías requeridas. **No uses la terminal del sistema (CMD/PowerShell)**, hazlo desde Thonny:

1. Ve al menú superior y selecciona **Herramientas (Tools)** > **Gestionar paquetes... (Manage packages...)**.
2. En la barra de búsqueda, busca e instala **uno por uno** los siguientes paquetes:
   - `vosk` (Para la conversión de voz a texto offline).
   - `sounddevice` (Para la captura de audio del micrófono).
   - `pyttsx3` (Para la síntesis de texto a voz).
   - `numpy` (Requerido para la manipulación de audio).

### 3. Descargar el Modelo Acústico de Vosk (Offline STT)
Para que el asistente pueda escucharte sin internet, requiere un modelo de lenguaje en español.
1. Ve a [Vosk Models](https://alphacephei.com/vosk/models).
2. Descarga el modelo pequeño para español: **`vosk-model-small-es-0.42`**.
3. Extrae el archivo ZIP.
4. Renombra la carpeta extraída como `modelo_vosk` y colócala en la raíz de este proyecto (la misma carpeta donde está `main.py`).

### 4. Inicializar y Ejecutar
1. En Thonny, abre el archivo `inicializar_datos.py` y presiona **Ejecutar (F5)**. Esto creará la base de datos `conocimiento.db` y precargará los conocimientos básicos, sinónimos y alias fonéticos.
2. Abre `main.py` y presiona **Ejecutar (F5)** para lanzar la interfaz principal.

---

## Arquitectura

* **`audio/`**: Contiene la lógica del micrófono, Speech-to-Text (`stt.py`) y Text-to-Speech (`tts.py`).
* **`conocimiento/`**: Gestión de persistencia local. Capa de abstracción para la DB SQLite.
* **`entrenamiento/`**: Funciones encargadas de inyectar nuevo conocimiento.
* **`experto/`**: Cerebro del sistema. Contiene el normalizador fonético, el analizador de reglas, y el motor de consultas principales.
* **`interfaz/`**: Interfaz de usuario construida con Tkinter (Dark Theme).
* **`docs/`**: Contiene toda la auditoría técnica, casos de uso, guías y documentación de migración a hardware embebido.
