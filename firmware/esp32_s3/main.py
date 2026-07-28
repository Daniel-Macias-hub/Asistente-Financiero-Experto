# ==============================================================================
# FIRMWARE DEFINITIVO ESP32-S3 (BASADO 100% EN test_grabadora.py)
# Hardware: PCB MRD085A / Kit OKYN-G5806 (ESP32-S3 N16R8)
# UART ligera sólo para comandos cortos. Cero envío de audio pesado por Serie.
# ==============================================================================
import machine  # pyrefly: ignore [missing-import] # type: ignore
from machine import Pin, I2S  # pyrefly: ignore [missing-import] # type: ignore
import ssd1306  # pyrefly: ignore [missing-import] # type: ignore
import time
import struct
import sys
import math
import uselect  # pyrefly: ignore [missing-import] # type: ignore
import gc

def safe_flush():
    """Flush seguro de sys.stdout para compatibilidad con MicroPython."""
    if hasattr(sys.stdout, 'flush'):
        try:
            sys.stdout.flush()
        except Exception:
            pass

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
    sys.stdout.write(f"[OLED ERR] {e}\n")
    safe_flush()

# Apagar LED blanco Neopixel
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
audio_in = None
try:
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
except Exception as e:
    sys.stdout.write(f"[MIC ERR] {e}\n")
    safe_flush()

audio_out = None
try:
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
except Exception as e:
    sys.stdout.write(f"[SPK ERR] {e}\n")
    safe_flush()

# BÚFER Y LÓGICA DE GRABACIÓN Y REPRODUCCIÓN LOCAL
audio_ram = bytearray(BUFFER_SIZE_16BIT)
read_buf = bytearray(512)

def correr_grabacion():
    """Ejecuta exactamente la lógica validada de test_grabadora.py."""
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
    if audio_in:
        for _ in range(5):
            audio_in.readinto(temp)

    bytes_written = 0
    while bytes_written < BUFFER_SIZE_16BIT:
        if audio_in:
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
    """Ejecuta exactamente la lógica validada de test_grabadora.py."""
    if oled:
        oled.fill(0)
        oled.rect(0, 0, 128, 64, 1)
        oled.text(" 🟢 REPRODUCIENDO ", 4, 15, 1)
        oled.text("Escucha la bocina", 4, 38, 1)
        oled.show()

    if audio_out:
        audio_out.write(audio_ram)
        time.sleep(0.1)

def reproducir_tono_audio():
    """Reproduce tono de prueba 440 Hz en MAX98357A."""
    if not audio_out: return
    freq = 440
    amplitude = 12000
    tone_buf = bytearray(1024)
    for i in range(512):
        s = int(amplitude * math.sin(2 * math.pi * freq * (i / SAMPLE_RATE)))
        struct.pack_into("<h", tone_buf, i * 2, s)
    for _ in range(30):
        audio_out.write(tone_buf)
    time.sleep(0.1)

def mostrar_idle():
    if not oled: return
    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)
    oled.text("ASISTENTE FIN.", 8, 15, 1)
    oled.text("Listo en PC", 18, 35, 1)
    oled.show()

def animacion_escuchando():
    if not oled: return
    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)
    oled.text("🔴 ESCUCHANDO", 12, 20, 1)
    oled.show()

def animacion_procesando():
    if not oled: return
    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)
    oled.text("⚙ PROCESANDO", 12, 20, 1)
    oled.show()

def animacion_respondiendo():
    if not oled: return
    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)
    oled.text("🔊 RESPONDIENDO", 8, 20, 1)
    oled.show()

# ==============================================================================
# BUCLE PRINCIPAL (Disparado únicamente por comandos UART cortos)
# ==============================================================================
def main():
    poll_obj = uselect.poll()
    poll_obj.register(sys.stdin, uselect.POLLIN)
    mostrar_idle()

    gc.collect()
    sys.stdout.write(f"[ESP32-S3] READY (RAM libre: {gc.mem_free()} B)\n")
    safe_flush()

    while True:
        try:
            events = poll_obj.poll(40)
            for _, flag in events:
                if flag & uselect.POLLIN:
                    linea = sys.stdin.readline().strip()
                    if not linea:
                        continue

                    if linea == "PING":
                        sys.stdout.write("PONG\n")
                        safe_flush()
                    elif linea == "OLED_TEST":
                        if oled:
                            oled.fill(0)
                            oled.rect(0, 0, 128, 64, 1)
                            oled.text("✓ OLED OK", 28, 25, 1)
                            oled.show()
                            time.sleep(1)
                            mostrar_idle()
                        sys.stdout.write("OLED_TEST_OK\n")
                        safe_flush()
                    elif linea == "AUDIO_TEST":
                        reproducir_tono_audio()
                        mostrar_idle()
                        sys.stdout.write("AUDIO_TEST_OK\n")
                        safe_flush()
                    elif linea in ("MIC_START", "MIC_TEST"):
                        correr_grabacion()
                        correr_reproduccion()
                        mostrar_idle()
                        sys.stdout.write("MIC_TEST_OK\n")
                        safe_flush()
                    elif linea.startswith("STATE:"):
                        partes = linea.split(":")
                        st = partes[1].upper() if len(partes) >= 2 else "IDLE"
                        if st == "ESCUCHANDO":
                            animacion_escuchando()
                        elif st == "PROCESANDO":
                            animacion_procesando()
                        elif st == "RESPONDIENDO":
                            animacion_respondiendo()
                        else:
                            mostrar_idle()
                        sys.stdout.write(f"STATE_ACK:{st}\n")
                        safe_flush()

            time.sleep(0.02)
        except Exception as err:
            sys.stdout.write(f"[MAIN ERR] {err}\n")
            safe_flush()

if __name__ == "__main__":
    main()
