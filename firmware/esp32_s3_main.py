# ==============================================================================
# FIRMWARE ESP32-S3 — PRODUCCIÓN ESTABLE
# Hardware: PCB MRD085A / Kit OKYN-G5806 (ESP32-S3 N16R8)
# Tono suavizado con fade, AUDIO_PLAY con buffer único RAM, OLED_ANIM añadido
# ==============================================================================
import machine  # pyrefly: ignore [missing-import] # type: ignore
from machine import Pin, I2S  # pyrefly: ignore [missing-import] # type: ignore
import ssd1306  # pyrefly: ignore [missing-import] # type: ignore
import time
import struct
import sys
import math
import ubinascii  # pyrefly: ignore [missing-import] # type: ignore

def safe_flush():
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
I2S_SPK_WS  = 16
I2S_SPK_SD  = 7
I2S_MIC_SCK = 5
I2S_MIC_WS  = 4
I2S_MIC_SD  = 6
SAMPLE_RATE       = 16000
RECORD_SECS       = 3
BUFFER_SIZE_16BIT = SAMPLE_RATE * 2 * RECORD_SECS  # 96 000 bytes

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
# INICIALIZACIÓN I2S (MICRÓFONO RX + BOCINA TX)
# ==============================================================================
audio_in = None
try:
    audio_in = I2S(0, sck=Pin(I2S_MIC_SCK), ws=Pin(I2S_MIC_WS), sd=Pin(I2S_MIC_SD),
                   mode=I2S.RX, bits=32, format=I2S.MONO, rate=SAMPLE_RATE, ibuf=1024)
    sys.stdout.write(f"[I2S RX OK] rate={SAMPLE_RATE}, bits=32, ibuf=1024\n")
    safe_flush()
except Exception as e_mic:
    sys.stdout.write(f"[I2S RX ERR] {e_mic}\n")
    safe_flush()

audio_out = None
try:
    audio_out = I2S(1, sck=Pin(I2S_SPK_SCK), ws=Pin(I2S_SPK_WS), sd=Pin(I2S_SPK_SD),
                    mode=I2S.TX, bits=16, format=I2S.MONO, rate=SAMPLE_RATE, ibuf=4096)
    sys.stdout.write(f"[I2S TX OK] rate={SAMPLE_RATE}, bits=16, ibuf=4096\n")
    safe_flush()
except Exception as e_spk:
    sys.stdout.write(f"[I2S TX ERR] {e_spk}\n")
    safe_flush()

audio_ram = bytearray(BUFFER_SIZE_16BIT)
read_buf  = bytearray(512)

# ==============================================================================
# FUNCIONES DE AUDIO Y ANIMACIÓN
# ==============================================================================
def reproducir_tono_audio():
    """Tono limpio de 440 Hz con fade-in y fade-out de 20 ms. Amplitud conservadora."""
    sys.stdout.write("[AUDIO_TEST] Generando tono 440 Hz (fade 20ms, amplitude=8000)...\n")
    safe_flush()
    if not audio_out:
        raise RuntimeError("audio_out is None")

    if oled:
        oled.fill(0)
        oled.rect(0, 0, 128, 64, 1)
        oled.text("  BOCINA TEST", 14, 18, 1)
        oled.text("  440 Hz", 32, 38, 1)
        oled.show()

    N        = SAMPLE_RATE          # 1 segundo = 16000 muestras
    AMP      = 8000                 # 24% del rango → limpio sin saturar
    FADE_N   = int(SAMPLE_RATE * 0.020)  # 20 ms de fade
    tone_buf = bytearray(N * 2)
    for i in range(N):
        raw = AMP * math.sin(2 * math.pi * 440 * i / SAMPLE_RATE)
        # Fade-in
        if i < FADE_N:
            raw *= i / FADE_N
        # Fade-out
        elif i > N - FADE_N:
            raw *= (N - i) / FADE_N
        struct.pack_into("<h", tone_buf, i * 2, int(raw))

    audio_out.write(tone_buf)
    time.sleep(1.0)   # Esperar que el DMA vacíe el buffer

def correr_grabacion():
    sys.stdout.write("[STEP 4] Entrando correr_grabacion con conteo previo 3-2-1\n")
    safe_flush()
    if not audio_in:
        raise RuntimeError("audio_in is None")

    for i in range(len(audio_ram)):
        audio_ram[i] = 0

    for countdown in range(3, 0, -1):
        if oled:
            oled.fill(0)
            oled.rect(0, 0, 128, 64, 1)
            oled.text("GRABANDO EN...", 12, 15, 1)
            oled.text(f"      {countdown}", 12, 35, 1)
            oled.show()
        time.sleep(0.8)

    if oled:
        oled.fill(0)
        oled.rect(0, 0, 128, 64, 1)
        oled.text(" GRABANDO ", 22, 15, 1)
        oled.text("HABLA AHORA!", 14, 38, 1)
        oled.show()

    temp = bytearray(256)
    for _ in range(5):
        audio_in.readinto(temp)

    bytes_written = 0
    t0 = time.time()
    while bytes_written < BUFFER_SIZE_16BIT:
        num_read = audio_in.readinto(read_buf)
        if num_read > 0:
            ns = num_read // 4
            for s in range(ns):
                if bytes_written >= BUFFER_SIZE_16BIT:
                    break
                v32 = struct.unpack("<i", read_buf[s*4:(s+1)*4])[0]
                v16 = max(-32768, min(32767, v32 >> 12))
                struct.pack_into("<h", audio_ram, bytes_written, v16)
                bytes_written += 2

    dur = time.time() - t0
    sys.stdout.write(f"[STEP 5] bytes_written={bytes_written} (dur={dur:.2f}s)\n")
    safe_flush()

    num_s = bytes_written // 2
    total_sq = 0
    min_v, max_v = 32767, -32768
    samples16 = []
    for i in range(min(16, num_s)):
        sv = struct.unpack_from("<h", audio_ram, i * 2)[0]
        samples16.append(sv)
    for i in range(0, bytes_written, 2):
        sv = struct.unpack_from("<h", audio_ram, i)[0]
        if sv < min_v: min_v = sv
        if sv > max_v: max_v = sv
        total_sq += sv * sv
    rms = math.sqrt(total_sq / max(1, num_s))

    sys.stdout.write(f"[STEP 5.1] Muestras_16={samples16}, Min={min_v}, Max={max_v}, RMS={rms:.2f}\n")
    safe_flush()

    if bytes_written < BUFFER_SIZE_16BIT:
        raise RuntimeError(f"bytes_written incompleto: {bytes_written}/{BUFFER_SIZE_16BIT}")

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
        oled.text(" REPRODUCIENDO", 8, 15, 1)
        oled.text("Escucha bocina", 10, 38, 1)
        oled.show()

    bytes_sent = audio_out.write(audio_ram)
    sys.stdout.write(f"[STEP 8] audio_out.write terminado: bytes_sent={bytes_sent}\n")
    safe_flush()
    time.sleep(3.0)   # Esperar que el DMA vacíe los 3 segundos
    sys.stdout.write("[STEP 9] Saliendo correr_reproduccion\n")
    safe_flush()

def animacion_osciloscopio():
    """Animación tipo osciloscopio: dibuja una onda sinusoidal desplazada."""
    if not oled:
        return
    N = 128
    for frame in range(12):
        oled.fill(0)
        oled.rect(0, 0, 128, 64, 1)
        # Onda sinusoidal centrada
        offset = frame * 6
        for x in range(1, N - 1):
            y1 = int(32 + 22 * math.sin(2 * math.pi * (x + offset) / 40))
            y2 = int(32 + 22 * math.sin(2 * math.pi * (x + 1 + offset) / 40))
            if 0 < y1 < 63 and 0 < y2 < 63:
                oled.line(x, y1, x + 1, y2, 1)
        oled.show()
        time.sleep(0.08)
    # Pantalla final: ASISTENTE centrado
    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)
    oled.text("  ASISTENTE", 14, 26, 1)
    oled.show()
    time.sleep(1.5)

def mostrar_idle():
    if not oled: return
    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)
    oled.text("ASISTENTE FIN.", 8, 15, 1)
    oled.text("Listo en PC", 18, 35, 1)
    oled.show()

# ==============================================================================
# BUCLE PRINCIPAL
# ==============================================================================
sys.stdout.write("[ESP32-S3] READY (v2.0 Production Stable)\n")
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
            # Secuencia rápida de estados (diagnóstico visual)
            sys.stdout.write("[OLED_TEST] Secuencia animada...\n")
            safe_flush()
            if oled:
                for txt in ["INICIANDO...", "ESCUCHANDO", "PROCESANDO", "RESPONDIENDO", "OLED OK"]:
                    oled.fill(0)
                    oled.rect(0, 0, 128, 64, 1)
                    oled.text(txt, 10, 25, 1)
                    oled.show()
                    time.sleep(0.4)
                mostrar_idle()
            sys.stdout.write("OLED_TEST_OK\n")
            safe_flush()

        elif cmd == "OLED_ANIM":
            # Animación osciloscopio + pantalla ASISTENTE (botón Test OLED individual)
            sys.stdout.write("[OLED_ANIM] Iniciando animacion osciloscopio...\n")
            safe_flush()
            animacion_osciloscopio()
            mostrar_idle()
            sys.stdout.write("OLED_ANIM_OK\n")
            safe_flush()

        elif cmd == "AUDIO_TEST":
            sys.stdout.write("[AUDIO_TEST] Reproduciendo tono limpio 440 Hz...\n")
            safe_flush()
            reproducir_tono_audio()
            mostrar_idle()
            sys.stdout.write("AUDIO_TEST_OK\n")
            safe_flush()

        elif cmd in ("MIC_TEST", "MIC_START"):
            sys.stdout.write("[STEP 1] Entrando MIC_TEST\n")
            safe_flush()
            if not audio_in:
                sys.stdout.write("MIC_TEST_FAIL: audio_in is None\n")
                safe_flush()
                continue
            if not audio_out:
                sys.stdout.write("MIC_TEST_FAIL: audio_out is None\n")
                safe_flush()
                continue
            sys.stdout.write(f"[STEP 2] audio_in OK\n[STEP 3] audio_out OK\n")
            safe_flush()
            try:
                correr_grabacion()
                correr_reproduccion()
                mostrar_idle()
                sys.stdout.write("[STEP 10] Enviando MIC_TEST_OK\n")
                safe_flush()
                sys.stdout.write("MIC_TEST_OK\n")
                safe_flush()
            except Exception as ex:
                sys.stdout.write(f"MIC_TEST_FAIL: {ex}\n")
                safe_flush()

        elif cmd.startswith("AUDIO_PLAY:"):
            # Stream directo a DMA por chunks para evitar agotamiento de memoria RAM (heap) en MicroPython
            partes = cmd.split(":")
            total_bytes = int(partes[1]) if len(partes) >= 2 else 0

            if oled:
                oled.fill(0)
                oled.rect(0, 0, 128, 64, 1)
                oled.text(" RESPONDIENDO", 10, 20, 1)
                oled.text(" Voz IA", 34, 40, 1)
                oled.show()

            sys.stdout.write("AUDIO_PLAY_READY\n")
            safe_flush()

            bytes_recibidos = 0
            while bytes_recibidos < total_bytes:
                line_b64 = sys.stdin.readline()
                if not line_b64:
                    continue
                s = line_b64.strip()
                if s == "STOP" or s == "AUDIO_PLAY_END":
                    break
                try:
                    chunk = ubinascii.a2b_base64(s)
                    if audio_out and len(chunk) > 0:
                        audio_out.write(chunk)
                        bytes_recibidos += len(chunk)
                except Exception as ex_b64:
                    sys.stdout.write(f"[AUDIO_PLAY ERR] {ex_b64}\n")
                    safe_flush()

            mostrar_idle()
            sys.stdout.write("AUDIO_PLAY_OK\n")
            safe_flush()

        elif cmd.startswith("STATE:"):
            partes = cmd.split(":")
            st = partes[1].upper() if len(partes) >= 2 else "IDLE"
            if oled:
                oled.fill(0)
                oled.rect(0, 0, 128, 64, 1)
                if st == "ESCUCHANDO":
                    oled.text(" ESCUCHANDO", 14, 25, 1)
                elif st == "PROCESANDO":
                    oled.text(" PROCESANDO", 14, 25, 1)
                elif st == "RESPONDIENDO":
                    oled.text(" RESPONDIENDO", 8, 25, 1)
                else:
                    oled.text("ASISTENTE FIN.", 8, 15, 1)
                    oled.text("Listo en PC", 18, 35, 1)
                oled.show()
            sys.stdout.write(f"STATE_ACK:{st}\n")
            safe_flush()

    except Exception as err:
        sys.stdout.write(f"[MAIN ERR] {err}\n")
        safe_flush()
