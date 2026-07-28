# ==============================================================================
# EXPERIMENTO 1: BASE PURA DE test_grabadora.py + PROTOCOLO SERIE MÍNIMO
# Cero animaciones en paralelo, cero poll(), cero GC en reproducción.
# ==============================================================================
import machine  # pyrefly: ignore [missing-import] # type: ignore
from machine import Pin, I2S  # pyrefly: ignore [missing-import] # type: ignore
import ssd1306  # pyrefly: ignore [missing-import] # type: ignore
import time
import struct
import sys

# ==============================================================================
# CONFIGURACIÓN DE PINES (PCB MRD085A)
# ==============================================================================
OLED_SDA = 41
OLED_SCL = 42

I2S_SPK_SCK = 15
I2S_SPK_WS = 16
I2S_SPK_SD = 7

I2S_MIC_SCK = 5
I2S_MIC_WS = 4
I2S_MIC_SD = 6

SAMPLE_RATE = 16000
RECORD_SECS = 3
BUFFER_SIZE_16BIT = SAMPLE_RATE * 2 * RECORD_SECS  # 96,000 bytes

# ==============================================================================
# INICIALIZACIÓN DE LA PANTALLA OLED
# ==============================================================================
oled = None
try:
    i2c = machine.SoftI2C(scl=Pin(OLED_SCL), sda=Pin(OLED_SDA))
    oled = ssd1306.SSD1306_I2C(128, 64, i2c)
    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)
    oled.text("ASISTENTE FIN.", 8, 15, 1)
    oled.text("Listo en PC", 18, 35, 1)
    oled.show()
except Exception as e:
    print("OLED Error:", e)

# Apagar LEDs Neopixel
try:
    import neopixel  # pyrefly: ignore [missing-import] # type: ignore
    for p in [48, 38, 8]:
        np = neopixel.NeoPixel(Pin(p), 1)
        np[0] = (0, 0, 0)
        np.write()
except Exception:
    pass

# ==============================================================================
# INICIALIZACIÓN ÚNICA DE PUERTOS I2S (Idéntica a test_grabadora.py)
# ==============================================================================
audio_in = I2S(
    0,
    sck=Pin(I2S_MIC_SCK),
    ws=Pin(I2S_MIC_WS),
    sd=Pin(I2S_MIC_SD),
    mode=I2S.RX,
    bits=32,
    format=I2S.MONO,
    rate=SAMPLE_RATE,
    ibuf=1024
)

audio_out = I2S(
    1,
    sck=Pin(I2S_SPK_SCK),
    ws=Pin(I2S_SPK_WS),
    sd=Pin(I2S_SPK_SD),
    mode=I2S.TX,
    bits=16,
    format=I2S.MONO,
    rate=SAMPLE_RATE,
    ibuf=1024
)

audio_ram = bytearray(BUFFER_SIZE_16BIT)
read_buf = bytearray(512)

def correr_grabacion():
    """Ejecuta exactamente la lógica sin cambios de test_grabadora.py."""
    for i in range(len(audio_ram)):
        audio_ram[i] = 0

    if oled:
        oled.fill(0)
        oled.rect(0, 0, 128, 64, 1)
        oled.text(" 🔴 GRABANDO ", 15, 15, 1)
        oled.text("Habla ahora!", 16, 38, 1)
        oled.show()

    # Vaciar lecturas basura acumuladas antes de empezar
    temp = bytearray(256)
    for _ in range(5):
        audio_in.readinto(temp)

    bytes_written = 0
    while bytes_written < BUFFER_SIZE_16BIT:
        num_read = audio_in.readinto(read_buf)
        if num_read > 0:
            num_samples = num_read // 4
            for s_idx in range(num_samples):
                if bytes_written >= BUFFER_SIZE_16BIT:
                    break
                val_32 = struct.unpack("<i", read_buf[s_idx*4 : (s_idx+1)*4])[0]
                val_16 = val_32 >> 16
                struct.pack_into("<h", audio_ram, bytes_written, val_16)
                bytes_written += 2

def correr_reproduccion():
    """Ejecuta exactamente la lógica sin cambios de test_grabadora.py."""
    if oled:
        oled.fill(0)
        oled.rect(0, 0, 128, 64, 1)
        oled.text(" 🟢 REPRODUCIENDO ", 4, 15, 1)
        oled.text("Escucha la bocina", 4, 38, 1)
        oled.show()

    audio_out.write(audio_ram)
    time.sleep(0.1)

def mostrar_idle():
    if not oled: return
    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)
    oled.text("ASISTENTE FIN.", 8, 15, 1)
    oled.text("Listo en PC", 18, 35, 1)
    oled.show()

# ==============================================================================
# BUCLE PRINCIPAL EXPERIMENTO 1 (Protocolo serie directo sin sobrecarga)
# ==============================================================================
print("[ESP32-S3] READY (Experimento 1)")

while True:
    try:
        linea = sys.stdin.readline()
        if not linea:
            continue
        cmd = linea.strip()

        if cmd == "PING":
            print("PONG")
        elif cmd == "OLED_TEST":
            if oled:
                oled.fill(0)
                oled.rect(0, 0, 128, 64, 1)
                oled.text("✓ OLED OK", 28, 25, 1)
                oled.show()
                time.sleep(0.8)
                mostrar_idle()
            print("OLED_TEST_OK")
        elif cmd == "AUDIO_TEST":
            correr_reproduccion()
            mostrar_idle()
            print("AUDIO_TEST_OK")
        elif cmd in ("MIC_TEST", "MIC_START"):
            correr_grabacion()
            correr_reproduccion()
            mostrar_idle()
            print("MIC_TEST_OK")
    except Exception as err:
        print("[ERR]", err)
