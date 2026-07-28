# 🤖 ASISTENTE EDUCATIVO Y FINANCIERO EXPERTO (ESP32-S3 + IA VISIÓN + I2S AUDIO)

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![MicroPython](https://img.shields.io/badge/MicroPython-ESP32--S3-red.svg)
![Status](https://img.shields.io/badge/Hardware-Verificado_100%25-brightgreen.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

Sistema embebido inteligente y suite de escritorio para educación financiera, análisis bursátil y reconocimiento de divisas mediante visión por computadora. El sistema opera con un circuito físico autónomo (**ESP32-S3 N16R8**) equipado con micrófono I2S, amplificador I2S, pantalla OLED y visión streaming en tiempo real vía **ESP32-CAM**.

---

## 📐 ARQUITECTURA Y DIAGRAMA DE CONEXIÓN DE PINES (PCB MRD085A / ESP32-S3)

### 🔌 Diagrama de Pines (Pinout Master)

#### 1. Pantalla OLED SSD1306 (SoftI2C)
| ESP32-S3 Pin | SSD1306 OLED Pin | Función |
| :--- | :--- | :--- |
| **GPIO 41** | **SDA** | Datos I2C por software |
| **GPIO 42** | **SCL** | Reloj I2C por software |
| **3V3** | **VCC** | Alimentación 3.3V |
| **GND** | **GND** | Tierra común |

#### 2. Micrófono MEMS I2S INMP441 (Entrada de Audio)
| ESP32-S3 Pin | INMP441 Pin | Función |
| :--- | :--- | :--- |
| **GPIO 5** | **SCK (BCLK)** | Reloj de bits I2S 0 (RX) |
| **GPIO 4** | **WS (LRCK)** | Selección de canal I2S 0 |
| **GPIO 6** | **SD (DOUT)** | Datos serie de audio de entrada |
| **GND** | **L/R** | Canal Izquierdo (Mono) |
| **3V3** | **VDD** | Alimentación 3.3V |
| **GND** | **GND** | Tierra común |

#### 3. Amplificador I2S MAX98357A + Bocina 3W (Salida de Audio)
| ESP32-S3 Pin | MAX98357A Pin | Función |
| :--- | :--- | :--- |
| **GPIO 15** | **BCLK** | Reloj de bits I2S 1 (TX) |
| **GPIO 16** | **LRC** | Selección de canal I2S 1 |
| **GPIO 7** | **DIN** | Datos serie de audio de salida |
| **5V / 3V3** | **VIN** | Alimentación principal (Recomendado 5V) |
| **GND** | **GND** | Tierra común |
| **--** | **+ / -** | Conectar a los polos de la Bocina 4Ω/8Ω 3W |

#### 4. Cámara Remota ESP32-CAM (Visión por Computadora MJPEG)
* **Conexión:** Alimentación 5V/GND e IP asignada vía Wi-Fi local (Ejemplo: `http://192.168.3.135`).

---

## 🛠️ GUÍA DE MONTAJE Y CARGA DE FIRMWARE EN EL ESP32-S3

### Paso 1: Preparar Thonny IDE
1. Descarga e instala **[Thonny IDE](https://thonny.org/)**.
2. Conecta la placa **ESP32-S3** a tu computadora mediante un cable USB-C de datos.
3. En Thonny, ve a **Herramientas ➔ Opciones ➔ Intérprete** y selecciona:
   * **Intérprete:** `MicroPython (ESP32)`
   * **Puerto:** El puerto COM asignado (Ejemplo: `COM5`).

### Paso 2: Flashear el Firmware en la Memoria Flash del ESP32-S3
1. En Thonny, abre el archivo local del repositorio:
   📄 **`firmware/esp32_s3/main.py`**
2. Haz clic en **`Archivo` ➔ `Guardar como...` ➔ `Dispositivo MicroPython`**.
3. Nombra el archivo exactamente como **`main.py`** y presiona **Guardar**.
4. Haz clic en el botón rojo **`STOP`** en Thonny y presiona el botón **`RESET`** en la placa ESP32-S3.
5. **Importante:** Cierra Thonny completamente para liberar el puerto COM.

---

## 🚀 MONTAJE Y EJECUCIÓN DEL SISTEMA DE ESCRITORIO (PC)

### 1. Requisitos Previos (Python 3.9+)
Asegúrate de contar con Python 3.9 o superior en tu sistema Windows.

### 2. Instalación de Dependencias
Abre PowerShell en la carpeta raíz del proyecto y ejecuta:

```powershell
pip install pyttsx3 numpy opencv-python pillow requests yfinance sqlite3
```

### 3. Inicializar Base de Conocimientos
Ejecuta el script de inyección inicial de conocimientos financieros:

```powershell
$env:PYTHONPATH=".;firmware"; python inicializar_datos.py
```

### 4. Lanzar la Aplicación Principal
Ejecuta el Dashboard interactivo:

```powershell
$env:PYTHONPATH=".;firmware"; python main.py
```

---

## 📋 PASOS PARA VERIFICAR EL SISTEMA COMPLETO

1. En el **Dashboard de Operaciones**, selecciona tu puerto COM (Ej. `COM5`) y presiona **`🔌 Conectar`**.
2. Presiona el botón verde **`🟢 Probar Sistema Completo`**.
3. El sistema verificará automáticamente en secuencia:
   * **OLED:** Mostrará animaciones de estado (`🔴 ESCUCHANDO`, `⚙ PROCESANDO`, `🔊 RESPONDIENDO`).
   * **Bocina:** Emitirá el tono claro de 440 Hz por el amplificador MAX98357A.
   * **Micrófono:** Mostrará el conteo regresivo `3.. 2.. 1..` en pantalla, grabará tu voz por el INMP441 y la reproducirá nítidamente por la bocina del circuito.
   * **Cámara:** Mostrará la captura en tiempo real en el recuadro del Dashboard.
   * **Visión IA / ORB:** Detectará los descriptores de divisas/criptomonedas.
   * **API Financiera:** Consultará la cotización de mercado en tiempo real.
   * **Voz de la IA (TTS):** Emitirá la respuesta explicativa del Asistente **directamente por la bocina física de tu circuito**.

---

## 📁 ESTRUCTURA DEL PROYECTO

```text
asistente_financiero/
├── api_financiera/      # Clientes HTTP (CoinGecko, Yahoo Finance)
├── audio/               # Síntesis de voz (TTS) y procesamiento PCM
├── conocimiento/        # Base de datos SQLite y motor semántico
├── comunicacion_esp32.py # Protocolo serie UART/Base64 full-duplex con ESP32-S3
├── experto/             # Normalizador fonético y motor de inferencia de reglas
├── firmware/
│   └── esp32_s3/        # Firmware MicroPython definitivo para ESP32-S3 (main.py)
├── interfaz/            # Interfaz gráfica moderna en Tkinter (Dark Theme)
├── vision/              # Detector visual de patrones por computador (ORB)
├── main.py              # Punto de entrada principal de la aplicación
└── README.md            # Manual de montaje, wiring y operación
```
