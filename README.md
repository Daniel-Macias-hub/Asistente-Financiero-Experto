# 🤖 ASISTENTE EDUCATIVO Y FINANCIERO EXPERTO (ESP32-S3 + IA VISIÓN + I2S AUDIO)

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![MicroPython](https://img.shields.io/badge/MicroPython-ESP32--S3-red.svg)
![Status](https://img.shields.io/badge/Hardware-Verificado_100%25-brightgreen.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

Sistema embebido inteligente y suite de escritorio para educación financiera, análisis bursátil y reconocimiento de divisas/criptomonedas mediante visión por computadora y voz. El sistema opera con un circuito físico autónomo (**ESP32-S3 N16R8**) equipado con micrófono I2S, amplificador I2S, pantalla OLED y visión streaming en tiempo real vía **ESP32-CAM**.

---

## 🎯 DESCRIPCIÓN DEL PROYECTO

El **Asistente Financiero Experto** es una solución integral que combina hardware embebido, visión por computadora y modelos de inteligencia artificial para brindar asistencia en tiempo real sobre educación financiera, cotización de mercado y reconocimiento visual de criptomonedas y activos.

### Características Principales:
* **Entrada de Voz Física:** Captura de voz hablada mediante el micrófono I2S **INMP441**.
* **Salida de Audio en Circuito:** Reproducción de respuestas sintetizadas por el amplificador I2S **MAX98357A** y bocina de 3W.
* **Interfaz de Pantalla Embebida:** Animaciones de estado (Escuchando, Procesando, Respondiendo, Osciloscopio) en pantalla **OLED SSD1306**.
* **Visión Remota en Tiempo Real:** Transmisión MJPEG y fotos con Flash LED vía **ESP32-CAM**.
* **Reconocimiento Visual IA:** Detección de patrones visuales de logotipos cripto con el detector de características **ORB** y **Google Gemini Vision**.
* **Dashboard Profesional (Estilo Bloomberg / TradingView):** Interfaz en **Tkinter** con tema oscuro, métricas en tiempo real, consola de trazabilidad serie y asistente de diagnóstico interactivo de 7 pasos.

---

## 📐 ARQUITECTURA Y FLUJO DEL SISTEMA

### Separación Estricta de Responsabilidades:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          ESP32-S3 (Circuito Físico)                     │
│  - Pantalla OLED SSD1306 (SoftI2C)                                     │
│  - Micrófono MEMS INMP441 (I2S RX 16kHz)                               │
│  - Amplificador MAX98357A + Bocina 3W (I2S TX 16kHz)                    │
│  - Control de Estados & Animaciones                                    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ UART Serial (115200 baud / Base64)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        PC (Aplicación de Escritorio)                    │
│  - Interfaz Gráfica Tkinter (Tema Dark Bloomberg)                       │
│  - Visión IA (Detector ORB + Gemini Vision)                            │
│  - Consultas Financieras (CoinGecko / yFinance)                        │
│  - Motor Experto & Base de Conocimientos (SQLite)                      │
│  - Reconocimiento y Síntesis de Voz (Vosk STT + Microsoft Sabina TTS)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / MJPEG Stream (Wi-Fi Local)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         ESP32-CAM (Visión Remota)                      │
│  - Cámara OV2640 (MJPEG Video Stream)                                  │
│  - Control de Flash LED (/led?state=1|0)                               │
│  - Captura Fotográfica (/capture)                                      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 HARDWARE UTILIZADO Y PINOUT MASTER (ESP32-S3 N16R8)

### 1. Pantalla OLED SSD1306 (SoftI2C)
| ESP32-S3 Pin | SSD1306 OLED Pin | Función |
| :--- | :--- | :--- |
| **GPIO 41** | **SDA** | Datos I2C por software |
| **GPIO 42** | **SCL** | Reloj I2C por software |
| **3V3** | **VCC** | Alimentación 3.3V |
| **GND** | **GND** | Tierra común |

### 2. Micrófono MEMS I2S INMP441 (Entrada de Audio)
| ESP32-S3 Pin | INMP441 Pin | Función |
| :--- | :--- | :--- |
| **GPIO 5** | **SCK (BCLK)** | Reloj de bits I2S 0 (RX) |
| **GPIO 4** | **WS (LRCK)** | Selección de canal I2S 0 |
| **GPIO 6** | **SD (DOUT)** | Datos serie de audio de entrada |
| **GND** | **L/R** | Canal Izquierdo (Mono) |
| **3V3** | **VDD** | Alimentación 3.3V |
| **GND** | **GND** | Tierra común |

### 3. Amplificador I2S MAX98357A + Bocina 3W (Salida de Audio)
| ESP32-S3 Pin | MAX98357A Pin | Función |
| :--- | :--- | :--- |
| **GPIO 15** | **BCLK** | Reloj de bits I2S 1 (TX) |
| **GPIO 16** | **LRC** | Selección de canal I2S 1 |
| **GPIO 7** | **DIN** | Datos serie de audio de salida |
| **5V / 3V3** | **VIN** | Alimentación principal (Recomendado 5V) |
| **GND** | **GND** | Tierra común |
| **--** | **+ / -** | Conectar a los polos de la Bocina 4Ω/8Ω 3W |

### 4. Cámara Remota ESP32-CAM (Visión por Computadora MJPEG)
* **Alimentación:** 5V / GND.
* **Red:** Conectada a la red Wi-Fi local asignando una IP fija (Ejemplo: `http://192.168.3.135`).

---

## 🛠️ TECNOLOGÍAS UTILIZADAS

* **Lenguajes:** Python 3.9+, MicroPython (ESP32-S3 v1.20+)
* **Librerías de Visión:** OpenCV (`cv2`), NumPy, PIL (Pillow)
* **Modelos de IA:** Google Gemini API (Gemini 1.5 Flash / Vision)
* **Audio y Voz:** Vosk (STT offline), Microsoft Speech API (`pyttsx3` / Sabina)
* **Base de Datos:** SQLite3 (`conocimiento.db`)
* **Mercados Financieros:** CoinGecko API, Yahoo Finance (`yfinance`)
* **Interfaz de Usuario:** Python Tkinter (Estilos personalizados `ttk` Bloomberg Terminal)

---

## ⚙️ CONFIGURACIÓN E INSTALACIÓN DESDE CERO

### 1. Clonar el Repositorio
```powershell
git clone https://github.com/Daniel-Macias-hub/Asistente-Financiero-Experto.git
cd Asistente-Financiero-Experto
```

### 2. Cargar Firmware en el ESP32-S3
1. Abre **[Thonny IDE](https://thonny.org/)**.
2. Conecta el **ESP32-S3** por cable USB.
3. Ve a `Herramientas -> Opciones -> Intérprete` -> Selecciona `MicroPython (ESP32)` y el puerto COM (ej. `COM5`).
4. Abre `firmware/esp32_s3/main.py`.
5. Haz clic en `Archivo -> Guardar como... -> Dispositivo MicroPython` con el nombre `/main.py`.
6. Presiona el botón `RESET` en la placa ESP32-S3 y **cierra Thonny** para liberar el puerto serie.

### 3. Configuración de Variables de Entorno (`.env` / `config.py`)
Si deseas utilizar la visión avanzada con Gemini Vision, define tu API Key en el archivo `.env`:
```env
GEMINI_API_KEY=tu_api_key_aqui
```

### 4. Instalación de Dependencias de Python en la PC
```powershell
pip install pyttsx3 numpy opencv-python pillow requests yfinance sqlite3 google-generativeai
```

### 5. Inicialización de Datos y Ejecución
```powershell
# 1. Inicializar base de datos SQLite
$env:PYTHONPATH=".;firmware"; python inicializar_datos.py

# 2. Ejecutar la aplicación principal
$env:PYTHONPATH=".;firmware"; python main.py
```

---

## 📋 ASISTENTE DE DIAGNÓSTICO Y COMPROBACIÓN

Al presionar el botón **`🟢 Probar Sistema Completo`** en el Dashboard, la aplicación ejecuta una secuencia automatizada de 7 pasos con indicación visual semafórica (🟡 Ejecutando -> 🟢 Correcto -> 🔴 Error), barra de progreso y generación de un reporte al finalizar:

1. **Paso 1/7 - OLED SSD1306:** Envío de secuencia de prueba animada al display.
2. **Paso 2/7 - Bocina MAX98357A:** Emisión de un tono sinusoidal limpio de 440 Hz con suave fade-in/fade-out de 20 ms.
3. **Paso 3/7 - Micrófono INMP441:** Conteo regresivo `3.. 2.. 1..` en OLED, grabación de 3s de voz, cálculo de métricas RMS reales y reproducción local en la bocina.
4. **Paso 4/7 - Cámara ESP32-CAM:** Encendido de Flash LED, captura fotográfica vía HTTP `/capture`, apagado de LED, visualización en pantalla y guardado en `capturas/YYYY-MM-DD_HH-MM-SS.jpg`.
5. **Paso 5/7 - Visión IA / ORB:** Análisis de descriptores visuales sobre la imagen capturada.
6. **Paso 6/7 - API Financiera:** Consulta en tiempo real de la cotización de Bitcoin en CoinGecko/yFinance.
7. **Paso 7/7 - Síntesis de Voz (TTS):** Transmisión de la voz explicativa del Asistente codificada en PCM **directamente a la bocina del circuito**.

---

## ⚠️ PROBLEMAS CONOCIDOS Y LIMITACIONES

1. **Puerto Serie Retenido por Thonny:**
   * Si Thonny está abierto o conectado a `COM5`, la aplicación de PC no podrá conectarse. **Solución:** Cerrar Thonny antes de ejecutar `main.py`.
2. **Subred Wi-Fi de la ESP32-CAM:**
   * La ESP32-CAM y la PC deben estar conectadas a la misma red Wi-Fi local para la correcta transmisión del stream MJPEG.
3. **Buffer de Audio DMA:**
   * La transmisión de voz sintetizada requiere enviar el bloque PCM completo antes del buffer I2S para evitar parpadeos en el altavoz. Esto ha sido corregido en la versión actual mediante buffer único en RAM.

---

## 📜 LICENCIA Y AUTORÍA

Proyecto desarrollado para la materia de Sistemas Inteligentes / Inteligencia de Negocios.
Licencia MIT.
