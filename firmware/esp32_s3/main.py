# ==============================================================================
# FIRMWARE ARQUITECTURA STREAMING ESP32-S3 (PCB MRD085A / Kit OKYN-G5806)
# Memoria ultra-optimizada sin grandes búferes globales (Cero MemoryError)
# Micrófono INMP441 + Bocina MAX98357A + OLED SSD1306 + Control Serial UART
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

# ------------------------------------------------------------------------------
# Configuración de Pines Hardware (PCB MRD085A)
# ------------------------------------------------------------------------------
OLED_SDA = 41
OLED_SCL = 42

I2S_MIC_SCK = 5
I2S_MIC_WS  = 4
I2S_MIC_SD  = 6

I2S_SPK_SCK = 15
I2S_SPK_WS  = 16
I2S_SPK_SD  = 7

SAMPLE_RATE = 16000
RECORD_SECS = 4
TOTAL_BYTES_RECORD = SAMPLE_RATE * 2 * RECORD_SECS  # 128,000 bytes para 4s

# Búferes estáticos ultra pequeños en RAM (máximo 512 bytes por búfer)
gc.collect()
READ_BUF = bytearray(512)   # Recibe 128 muestras de 32-bit I2S del mic INMP441
CONV_BUF = bytearray(256)   # Almacena 128 muestras de 16-bit PCM para streaming
TONE_BUF = bytearray(512)   # Genera bloques senoidales de 256 muestras 16-bit

# Verificación explícita de memoria libre
mem_free_boot = gc.mem_free()
sys.stdout.write(f"[FIRMWARE] RAM Libre al inicio: {mem_free_boot} bytes\n")
safe_flush()

# ------------------------------------------------------------------------------
# Inicialización Pantalla OLED SSD1306
# ------------------------------------------------------------------------------
oled = None
try:
    i2c = machine.SoftI2C(scl=Pin(OLED_SCL), sda=Pin(OLED_SDA))
    oled = ssd1306.SSD1306_I2C(128, 64, i2c)
except Exception as e_oled:
    sys.stdout.write(f"[OLED ERR] {e_oled}\n")
    safe_flush()

# Desactivar NeoPixels para ahorrar energía
try:
    import neopixel  # pyrefly: ignore [missing-import] # type: ignore
    for p in [48, 38, 8]:
        np = neopixel.NeoPixel(Pin(p), 1)
        np[0] = (0, 0, 0)
        np.write()
except Exception:
    pass

# ------------------------------------------------------------------------------
# Canales Audio I2S (0 RX: Micrófono / 1 TX: Bocina)
# ------------------------------------------------------------------------------
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
except Exception as e_mic:
    sys.stdout.write(f"[MIC ERR] {e_mic}\n")
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
except Exception as e_spk:
    sys.stdout.write(f"[SPK ERR] {e_spk}\n")
    safe_flush()

# ------------------------------------------------------------------------------
# Animaciones OLED SSD1306
# ------------------------------------------------------------------------------
def animacion_osciloscopio(titulo, frame, amplitud=14, frec=0.18):
    if not oled: return
    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)
    oled.text(titulo, 8, 6, 1)
    for x in range(4, 124, 8):
        oled.pixel(x, 40, 1)
    prev_x = 4
    prev_y = 40 + int(amplitud * math.sin((4 + frame * 6) * frec))
    for x in range(6, 124, 3):
        y = 40 + int(amplitud * math.sin((x + frame * 6) * frec) * math.cos(x * 0.04))
        oled.line(prev_x, prev_y, x, y, 1)
        prev_x, prev_y = x, y
    oled.show()

def animacion_iniciando(paso):
    if not oled: return
    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)
    oled.text("INICIANDO...", 18, 15, 1)
    ancho = ((paso % 10) + 1) * 10
    oled.rect(14, 38, 100, 10, 1)
    oled.fill_rect(14, 38, ancho, 10, 1)
    oled.show()

def animacion_escuchando(frame):
    animacion_osciloscopio("🔴 ESCUCHANDO", frame, amplitud=16, frec=0.20)

def animacion_procesando(frame):
    if not oled: return
    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)
    oled.text("⚙ PROCESANDO", 12, 12, 1)
    dots = "." * ((frame % 4) + 1)
    oled.text(f"Pensando{dots}", 18, 30, 1)
    animacion_osciloscopio("⚙ PROCESANDO", frame, amplitud=6, frec=0.10)

def animacion_respondiendo(frame):
    animacion_osciloscopio("🔊 RESPONDIENDO", frame, amplitud=20, frec=0.28)

def animacion_error(mensaje="ERR SISTEMA"):
    if not oled: return
    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)
    oled.text("❌ ERROR", 30, 15, 1)
    oled.text(mensaje[:14], 8, 38, 1)
    oled.show()

def mostrar_idle():
    if not oled: return
    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)
    oled.text("ASISTENTE FIN.", 8, 15, 1)
    oled.text("Listo en PC", 18, 32, 1)
    for x in range(10, 118, 4):
        y = 52 + int(3 * math.sin(x * 0.1))
        oled.pixel(x, y, 1)
    oled.show()

# ------------------------------------------------------------------------------
# Pruebas y Streaming de Audio (Sin reservas masivas de memoria RAM)
# ------------------------------------------------------------------------------
def ejecutar_test_oled_secuencia():
    sys.stdout.write("[TEST] OLED Secuencia...\n")
    safe_flush()
    estados = [
        ("INICIANDO", animacion_iniciando),
        ("ESCUCHANDO", animacion_escuchando),
        ("PROCESANDO", animacion_procesando),
        ("RESPONDIENDO", animacion_respondiendo),
        ("LISTO", lambda p: animacion_osciloscopio("✓ OLED OK", p, amplitud=12))
    ]
    for _, func in estados:
        t_start = time.time()
        f = 0
        while time.time() - t_start < 0.8:
            func(f)
            f += 1
            time.sleep(0.04)
    mostrar_idle()
    sys.stdout.write("OLED_TEST_OK\n")
    safe_flush()

def reproducir_tono_prueba_audio():
    """Genera tono senoidal de 440 Hz en bloques de 512 bytes sin usar búfer global masivo."""
    sys.stdout.write("[TEST] Tono de prueba 440 Hz en streaming...\n")
    safe_flush()
    if not audio_out:
        sys.stdout.write("AUDIO_TEST_ERR\n")
        safe_flush()
        return

    gc.collect()
    freq = 440
    amplitude = 12000
    total_samples = SAMPLE_RATE  # 1 segundo = 16,000 muestras
    samples_done = 0

    while samples_done < total_samples:
        to_gen = min(256, total_samples - samples_done)
        for i in range(to_gen):
            s_idx = samples_done + i
            sample = int(amplitude * math.sin(2 * math.pi * freq * (s_idx / SAMPLE_RATE)))
            struct.pack_into("<h", TONE_BUF, i * 2, sample)
        audio_out.write(TONE_BUF[:to_gen * 2])
        samples_done += to_gen

    time.sleep(0.1)
    sys.stdout.write("AUDIO_TEST_OK\n")
    safe_flush()
    gc.collect()

def reproducir_audio_pcm_stream(total_bytes):
    """Recibe flujo de audio PCM por Serial y lo proyecta a la bocina I2S MAX98357A."""
    if not audio_out or total_bytes <= 0:
        sys.stdout.write("AUDIO_PLAY_ERR\n")
        safe_flush()
        return

    sys.stdout.write(f"AUDIO_PLAY_READY:{total_bytes}\n")
    safe_flush()

    gc.collect()
    bytes_read = 0
    stdin_buf = sys.stdin.buffer if hasattr(sys.stdin, 'buffer') else sys.stdin

    while bytes_read < total_bytes:
        to_read = min(512, total_bytes - bytes_read)
        num_r = stdin_buf.readinto(READ_BUF, to_read)
        if num_r and num_r > 0:
            audio_out.write(READ_BUF[:num_r])
            bytes_read += num_r
        else:
            break

    sys.stdout.write("AUDIO_PLAY_OK\n")
    safe_flush()
    gc.collect()

def grabar_y_transmitir_mic():
    """Lee el micrófono INMP441 en bloques de 512B y transmite PCM por Serial inmediatamente."""
    if not audio_in:
        sys.stdout.write("MIC_DATA:0\n")
        safe_flush()
        return

    gc.collect()
    # Limpiar muestras residuales del búfer I2S
    for _ in range(3):
        audio_in.readinto(READ_BUF)

    sys.stdout.write(f"MIC_DATA:{TOTAL_BYTES_RECORD}\n")
    safe_flush()

    out_stream = sys.stdout.buffer if hasattr(sys.stdout, 'buffer') else sys.stdout
    bytes_written = 0

    while bytes_written < TOTAL_BYTES_RECORD:
        num_read = audio_in.readinto(READ_BUF)
        if num_read > 0:
            num_samples = num_read // 4
            out_idx = 0
            for s_idx in range(num_samples):
                if bytes_written + (out_idx * 2) >= TOTAL_BYTES_RECORD:
                    break
                val_32 = struct.unpack("<i", READ_BUF[s_idx*4 : (s_idx+1)*4])[0]
                val_16 = val_32 >> 16
                struct.pack_into("<h", CONV_BUF, out_idx * 2, val_16)
                out_idx += 1

            if out_idx > 0:
                bytes_to_send = out_idx * 2
                out_stream.write(CONV_BUF[:bytes_to_send])
                safe_flush()
                bytes_written += bytes_to_send

    safe_flush()
    gc.collect()

# ------------------------------------------------------------------------------
# Bucle Principal de Control Serial (Polling no bloqueante)
# ------------------------------------------------------------------------------
def main():
    poll_obj = uselect.poll()
    poll_obj.register(sys.stdin, uselect.POLLIN)

    estado_actual = "IDLE"
    frame_counter = 0
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
                        ejecutar_test_oled_secuencia()
                    elif linea == "AUDIO_TEST":
                        reproducir_tono_prueba_audio()
                    elif linea == "MIC_START":
                        grabar_y_transmitir_mic()
                    elif linea.startswith("AUDIO_PLAY:"):
                        try:
                            n_b = int(linea.split(":")[1])
                            reproducir_audio_pcm_stream(n_b)
                        except Exception as ex_p:
                            sys.stdout.write(f"AUDIO_PLAY_ERR:{ex_p}\n")
                            safe_flush()
                    elif linea.startswith("STATE:"):
                        partes = linea.split(":")
                        if len(partes) >= 2:
                            estado_actual = partes[1].upper()
                            sys.stdout.write(f"STATE_ACK:{estado_actual}\n")
                            safe_flush()

            frame_counter += 1
            if estado_actual == "INICIANDO":
                animacion_iniciando(frame_counter)
            elif estado_actual == "ESCUCHANDO":
                animacion_escuchando(frame_counter)
            elif estado_actual == "PROCESANDO":
                animacion_procesando(frame_counter)
            elif estado_actual == "RESPONDIENDO":
                animacion_respondiendo(frame_counter)
            elif estado_actual == "ERROR":
                animacion_error("FALLO SISTEMA")
            else:
                mostrar_idle()

            time.sleep(0.04)
        except Exception as err:
            sys.stdout.write(f"[MAIN ERR] {err}\n")
            safe_flush()
            time.sleep(0.2)

if __name__ == "__main__":
    main()
