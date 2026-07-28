# ==============================================================================
# FIRMWARE CON INSTRUMENTACIÓN COMPLETA DE DIAGNÓSTICO (ESP32-S3)
# Trazas obligatorias paso a paso por UART + Eliminación de excepciones ocultas
# ==============================================================================
import machine  # pyrefly: ignore [missing-import] # type: ignore
from machine import Pin, I2S  # pyrefly: ignore [missing-import] # type: ignore
import ssd1306  # pyrefly: ignore [missing-import] # type: ignore
import time
import struct
import sys
import math

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
# INICIALIZACIÓN ÚNICA DE PUERTOS I2S CON VERIFICACIÓN
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
    sys.stdout.write(f"[I2S RX OK] audio_in={audio_in}, rate={SAMPLE_RATE}, bits=32, ibuf=1024\n")
    safe_flush()
except Exception as e_mic:
    sys.stdout.write(f"[I2S RX ERR] {e_mic}\n")
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
    sys.stdout.write(f"[I2S TX OK] audio_out={audio_out}, rate={SAMPLE_RATE}, bits=16, ibuf=1024\n")
    safe_flush()
except Exception as e_spk:
    sys.stdout.write(f"[I2S TX ERR] {e_spk}\n")
    safe_flush()

audio_ram = bytearray(BUFFER_SIZE_16BIT)
read_buf = bytearray(512)

def correr_grabacion():
    sys.stdout.write("[STEP 4] Entrando correr_grabacion\n")
    safe_flush()

    if not audio_in:
        raise RuntimeError("audio_in is None")

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
    t0_rec = time.time()
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

    dur = time.time() - t0_rec
    sys.stdout.write(f"[STEP 5] bytes_written = {bytes_written} (tomó {dur:.2f}s)\n")
    safe_flush()

    # Calcular métricas de captura
    num_s = bytes_written // 2
    samples_16 = []
    total_sq = 0
    min_val = 32767
    max_val = -32768
    for i in range(min(16, num_s)):
        s_val = struct.unpack_from("<h", audio_ram, i * 2)[0]
        samples_16.append(s_val)

    for i in range(0, bytes_written, 2):
        s_val = struct.unpack_from("<h", audio_ram, i)[0]
        if s_val < min_val: min_val = s_val
        if s_val > max_val: max_val = s_val
        total_sq += s_val * s_val

    rms = math.sqrt(total_sq / max(1, num_s))
    sys.stdout.write(f"[STEP 5.1] Muestras_16={samples_16}, Min={min_val}, Max={max_val}, RMS={rms:.2f}\n")
    safe_flush()

    if bytes_written < BUFFER_SIZE_16BIT:
        raise RuntimeError(f"bytes_written incompleto: {bytes_written}/{BUFFER_SIZE_16BIT}")

    if rms < 1.0 and max_val == 0 and min_val == 0:
        raise RuntimeError(f"Silencio nulo capturado: RMS={rms:.2f}, Min={min_val}, Max={max_val}")

    sys.stdout.write("[STEP 6] Saliendo correr_grabacion\n")
    safe_flush()
    return bytes_written, rms

def correr_reproduccion():
    sys.stdout.write("[STEP 7] Entrando correr_reproduccion\n")
    safe_flush()

    if not audio_out:
        raise RuntimeError("audio_out is None")

    if oled:
        oled.fill(0)
        oled.rect(0, 0, 128, 64, 1)
        oled.text(" 🟢 REPRODUCIENDO ", 4, 15, 1)
        oled.text("Escucha la bocina", 4, 38, 1)
        oled.show()

    bytes_sent = audio_out.write(audio_ram)
    sys.stdout.write(f"[STEP 8] audio_out.write terminado: bytes_sent={bytes_sent}\n")
    safe_flush()
    time.sleep(0.1)

    sys.stdout.write("[STEP 9] Saliendo correr_reproduccion\n")
    safe_flush()

def mostrar_idle():
    if not oled: return
    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)
    oled.text("ASISTENTE FIN.", 8, 15, 1)
    oled.text("Listo en PC", 18, 35, 1)
    oled.show()

# ==============================================================================
# BUCLE PRINCIPAL CON TRAZABILIDAD OBLIGATORIA
# ==============================================================================
sys.stdout.write("[ESP32-S3] READY (Con Instrumentación de Diagnóstico paso a paso)\n")
safe_flush()

while True:
    try:
        linea = sys.stdin.readline()
        if not linea:
            continue
        cmd = linea.strip()

        if cmd == "PING":
            sys.stdout.write("PONG\n")
            safe_flush()
        elif cmd == "OLED_TEST":
            sys.stdout.write("[OLED_TEST] Iniciando secuencia...\n")
            safe_flush()
            if oled:
                oled.fill(0)
                oled.rect(0, 0, 128, 64, 1)
                oled.text("✓ OLED OK", 28, 25, 1)
                oled.show()
                time.sleep(0.8)
                mostrar_idle()
            sys.stdout.write("OLED_TEST_OK\n")
            safe_flush()
        elif cmd == "AUDIO_TEST":
            sys.stdout.write("[AUDIO_TEST] Iniciando prueba bocina...\n")
            safe_flush()
            correr_reproduccion()
            mostrar_idle()
            sys.stdout.write("AUDIO_TEST_OK\n")
            safe_flush()
        elif cmd in ("MIC_TEST", "MIC_START"):
            sys.stdout.write("[STEP 1] Entrando MIC_TEST\n")
            safe_flush()
            if audio_in:
                sys.stdout.write(f"[STEP 2] audio_in inicializado: {audio_in}\n")
            else:
                sys.stdout.write("MIC_TEST_FAIL: audio_in is None\n")
                safe_flush()
                continue

            if audio_out:
                sys.stdout.write(f"[STEP 3] audio_out inicializado: {audio_out}\n")
            else:
                sys.stdout.write("MIC_TEST_FAIL: audio_out is None\n")
                safe_flush()
                continue

            try:
                correr_grabacion()
                correr_reproduccion()
                mostrar_idle()
                sys.stdout.write("[STEP 10] Enviando MIC_TEST_OK\n")
                safe_flush()
                sys.stdout.write("MIC_TEST_OK\n")
                safe_flush()
            except Exception as ex_mic:
                sys.stdout.write(f"MIC_TEST_FAIL: {ex_mic}\n")
                safe_flush()
    except Exception as err:
        sys.stdout.write(f"[MAIN ERR] {err}\n")
        safe_flush()
