# Documentación de Pinout y Configuración - PCB MRD085A
*Kit de Chatbot por Voz / OKYN-G5806 (ESP32-S3 N16R8)*

Esta guía contiene la configuración exacta de hardware probada y validada para que puedas construir tus proyectos sin conflictos de pines.

---

## 1. Tabla de Pines Definitiva

| Componente | Señal de la Placa | GPIO del ESP32-S3 | Puerto / Bus | Notas de Configuración |
| :--- | :--- | :--- | :--- | :--- |
| **Pantalla OLED** | `SCL` | **`42`** | `SoftI2C` | Dirección I2C: `0x3C` (`60`). |
| **Pantalla OLED** | `SDA` | **`41`** | `SoftI2C` | Utilizar SoftI2C a 100 kHz. |
| **Bocina (MAX98357A)**| `BCLK` | **`15`** | `I2S 1` (TX) | Reloj de bits (Bit Clock). |
| **Bocina (MAX98357A)**| `WS` | **`16`** | `I2S 1` (TX) | Reloj de canal (LRCK). |
| **Bocina (MAX98357A)**| `DIN` | **`7`** | `I2S 1` (TX) | Línea de datos (Serial Data). |
| **Micrófono (INMP441)**| `SC` (SCK) | **`5`** | `I2S 0` (RX) | Reloj de bits (Bit Clock). |
| **Micrófono (INMP441)**| `WS` | **`4`** | `I2S 0` (RX) | Reloj de canal (LRCK). |
| **Micrófono (INMP441)**| `SD` | **`6`** | `I2S 0` (RX) | Línea de datos (Serial Data). |
| **LED RGB NeoPixel**  | `DIN` | **`48`, `38`, `8`**| `NeoPixel` | Apagar al inicio enviando `(0, 0, 0)`. |

---

## 2. Diagrama del Conexionado Físico del Micrófono

Asegúrate de que los cables dupont entre el micrófono INMP441 y la placa PCB MRD085A sigan estrictamente este orden:

```
  PCB (Lado Izquierdo)             Micrófono INMP441
┌─────────────────────┐          ┌───────────────────┐
│        SD (Pin 1)  ─┼──────────┼─>  SD             │
│        SC (Pin 2)  ─┼──────────┼─>  SCK            │
│        WS (Pin 3)  ─┼──────────┼─>  WS             │
│        LR (Pin 4)  ─┼──────────┼─>  L/R (GND)      │
│       GND (Pin 5)  ─┼──────────┼─>  GND            │
│      3.3V (Pin 6)  ─┼──────────┼─>  VDD            │
└─────────────────────┘          └───────────────────┘
```

---

## 3. Plantillas de Código Listas para Usar

### 🔧 Inicialización de Pantalla OLED (SoftI2C)
```python
import machine
import ssd1306

# Pines OLED
OLED_SDA = 41
OLED_SCL = 42

i2c = machine.SoftI2C(scl=machine.Pin(OLED_SCL), sda=machine.Pin(OLED_SDA))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# Escribir en pantalla
oled.fill(0)
oled.text("OLED OK", 10, 10, 1)
oled.show()
```

### 🎙️ Inicialización del Micrófono (INMP441)
*Nota: Se debe usar el canal de hardware `I2S(0)` para lectura (RX).*
```python
from machine import Pin, I2S

I2S_MIC_SCK = 5
I2S_MIC_WS = 4
I2S_MIC_SD = 6

audio_in = I2S(
    0, # Puerto I2S 0
    sck=Pin(I2S_MIC_SCK),
    ws=Pin(I2S_MIC_WS),
    sd=Pin(I2S_MIC_SD),
    mode=I2S.RX,
    bits=32,            # INMP441 requiere 32 bits de ancho de ranura
    format=I2S.MONO,
    rate=16000,
    ibuf=512            # Evita colgar memoria DMA
)

# Para leer:
# buf = bytearray(512)
# num_read = audio_in.readinto(buf)
```

### 🔊 Inicialización de la Bocina (MAX98357A)
*Nota: Se debe usar el canal de hardware `I2S(1)` para escritura (TX).*
```python
from machine import Pin, I2S

I2S_SPK_SCK = 15
I2S_SPK_WS = 16
I2S_SPK_SD = 7

audio_out = I2S(
    1, # Puerto I2S 1
    sck=Pin(I2S_SPK_SCK),
    ws=Pin(I2S_SPK_WS),
    sd=Pin(I2S_SPK_SD),
    mode=I2S.TX,
    bits=16,
    format=I2S.MONO,
    rate=16000,
    ibuf=1024
)

# Para reproducir:
# audio_out.write(buffer_audio_16bit)
```

### 💡 Apagar LEDs de Estado Integrados
```python
import neopixel
from machine import Pin

# Apagar leds NeoPixel en pines comunes del ESP32-S3
for pin_num in [48, 38, 8]:
    try:
        np = neopixel.NeoPixel(Pin(pin_num), 1)
        np[0] = (0, 0, 0)
        np.write()
    except Exception:
        pass
```
