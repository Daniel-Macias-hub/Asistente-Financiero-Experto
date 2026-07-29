# ==============================================================================
# FIRMWARE ESP32-S3 — PRODUCCIÓN Y PRUEBAS AVANZADAS
# Hardware: PCB MRD085A / Kit OKYN-G5806 (ESP32-S3 N16R8)
# OLED animado completo, Melodía MAX98357A, Grabación guiada 5s con Vúmetro, GC Heap
# ==============================================================================
import machine  # pyrefly: ignore [missing-import] # type: ignore
from machine import Pin, I2S  # pyrefly: ignore [missing-import] # type: ignore
import ssd1306  # pyrefly: ignore [missing-import] # type: ignore
import time
import struct
import sys
import math
import gc
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
RECORD_SECS       = 5
BUFFER_SIZE_16BIT = SAMPLE_RATE * 2 * RECORD_SECS  # 160 000 bytes (5s mono 16-bit)

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
                   mode=I2S.RX, bits=32, format=I2S.MONO, rate=SAMPLE_RATE, ibuf=2048)
    sys.stdout.write(f"[I2S RX OK] rate={SAMPLE_RATE}, bits=32, ibuf=2048\n")
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
# DIBUJO DE ICONOS Y CHECKMARKS EN OLED (BUFFER 128x64)
# ==============================================================================
def dibujar_icono_robot():
    """Dibuja el logotipo / icono pixel art del Asistente en el OLED."""
    if not oled: return
    oled.fill(0)
    # Cabeza robot (rectángulo)
    oled.rect(48, 12, 32, 26, 1)
    # Ojos
    oled.fill_rect(54, 20, 6, 6, 1)
    oled.fill_rect(68, 20, 6, 6, 1)
    # Antena
    oled.line(64, 4, 64, 12, 1)
    oled.fill_rect(62, 2, 5, 3, 1)
    # Boca / Pantalla
    oled.line(56, 32, 72, 32, 1)
    # Cuerpo
    oled.rect(42, 40, 44, 20, 1)
    oled.text("AI BOT", 48, 46, 1)
    oled.show()

def dibujar_checkmark_exito():
    """Dibuja un gran Checkmark (✔) de verificación en el OLED."""
    if not oled: return
    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)
    # Dibujar palomita gruesa ✔ (check)
    # Línea corta descendente
    for w in range(-2, 3):
        oled.line(36 + w, 32, 52 + w, 48, 1)
    # Línea larga ascendente
    for w in range(-2, 3):
        oled.line(52 + w, 48, 92 + w, 16, 1)

    oled.text("PRUEBA FINALIZADA", 4, 52, 1)
    oled.show()

# ==============================================================================
# FUNCIONES DE AUDIO Y MELODÍA RECONOCIBLE
# ==============================================================================
def reproducir_melodia_reconocible():
    """
    Sintetiza y reproduce una melodía musical reconocible de ~4 segundos
    ("Cumpleaños Feliz" / notas armónicas) con envolventes limpias de sine wave.
    """
    sys.stdout.write("[AUDIO_TEST] Generando melodía musical demostrativa de 4s...\n")
    safe_flush()
    if not audio_out:
        raise RuntimeError("audio_out is None")

    if oled:
        oled.fill(0)
        oled.rect(0, 0, 128, 64, 1)
        oled.text("  BOCINA TEST", 14, 15, 1)
        oled.text("  REPRODUCIENDO", 10, 32, 1)
        oled.text("  MELODIA 4s", 20, 48, 1)
        oled.show()

    # Notas de "Cumpleaños Feliz" (Frecuencia Hz, Duración ms)
    # C4=261.6, D4=293.7, E4=329.6, F4=349.2, G4=392.0, A4=440.0, C5=523.3
    notas = [
        (261.6, 250), (261.6, 250), (293.7, 450), (261.6, 450), (349.2, 450), (329.6, 750),
        (261.6, 250), (261.6, 250), (293.7, 450), (261.6, 450), (392.0, 450), (349.2, 750)
    ]

    AMP = 7500  # Vol conservador (limpio sin saturación)

    for freq, dur_ms in notas:
        num_samples = int(SAMPLE_RATE * (dur_ms / 1000.0))
        fade_samples = int(SAMPLE_RATE * 0.015)  # 15 ms envelope
        buf_note = bytearray(num_samples * 2)

        for i in range(num_samples):
            val = AMP * math.sin(2 * math.pi * freq * i / SAMPLE_RATE)
            # Envolvente Fade-in / Fade-out por nota
            if i < fade_samples:
                val *= (i / fade_samples)
            elif i > num_samples - fade_samples:
                val *= ((num_samples - i) / fade_samples)

            struct.pack_into("<h", buf_note, i * 2, int(val))

        audio_out.write(buf_note)
        time.sleep(0.02)  # Pausa breve entre notas

    time.sleep(0.5)

def correr_grabacion_guiada_5s():
    """Ejecuta la prueba de micrófono guiada de 5 segundos con Vúmetro en tiempo real."""
    sys.stdout.write("[MIC_TEST] Iniciando secuencia guiada 5 segundos con Vúmetro...\n")
    safe_flush()
    if not audio_in:
        raise RuntimeError("audio_in is None")

    for i in range(len(audio_ram)):
        audio_ram[i] = 0

    # 1. Título inicial
    if oled:
        oled.fill(0)
        oled.rect(0, 0, 128, 64, 1)
        oled.text("Prueba de", 28, 15, 1)
        oled.text("microfono", 28, 35, 1)
        oled.show()
        time.sleep(1.2)

    # 2. Conteo regresivo: 3... 2... 1... ¡YA!
    for countdown in range(3, 0, -1):
        if oled:
            oled.fill(0)
            oled.rect(0, 0, 128, 64, 1)
            oled.text("Iniciando en:", 14, 15, 1)
            oled.text(f"      {countdown}", 12, 38, 1)
            oled.show()
        time.sleep(0.8)

    if oled:
        oled.fill(0)
        oled.rect(0, 0, 128, 64, 1)
        oled.text("   ¡YA!", 36, 25, 1)
        oled.show()
        time.sleep(0.4)

    # Vaciar muestras residuales
    temp = bytearray(256)
    for _ in range(5):
        audio_in.readinto(temp)

    # 3. Grabación de 5 segundos con Vúmetro dinámico en OLED
    bytes_written = 0
    t0 = time.time()
    last_vumeter_update = 0

    while bytes_written < BUFFER_SIZE_16BIT:
        num_read = audio_in.readinto(read_buf)
        if num_read > 0:
            ns = num_read // 4
            chunk_max = 0
            for s in range(ns):
                if bytes_written >= BUFFER_SIZE_16BIT:
                    break
                v32 = struct.unpack("<i", read_buf[s*4:(s+1)*4])[0]
                v16 = max(-32768, min(32767, v32 >> 12))
                struct.pack_into("<h", audio_ram, bytes_written, v16)
                bytes_written += 2
                abs_v = abs(v16)
                if abs_v > chunk_max: chunk_max = abs_v

            # Actualizar Vúmetro en OLED cada 100 ms
            t_now = time.time()
            if oled and (t_now - last_vumeter_update > 0.10):
                last_vumeter_update = t_now
                seg_act = int(t_now - t0) + 1
                level_ratio = min(1.0, chunk_max / 16000.0)
                bar_w = int(level_ratio * 104)

                oled.fill(0)
                oled.rect(0, 0, 128, 64, 1)
                oled.text(f" GRABANDO ({seg_act}s/5s)", 8, 10, 1)
                # Marco de la barra de nivel
                oled.rect(12, 30, 104, 14, 1)
                # Relleno del Vúmetro
                if bar_w > 0:
                    oled.fill_rect(12, 30, bar_w, 14, 1)
                oled.show()

    dur = time.time() - t0
    sys.stdout.write(f"[STEP 5] bytes_written={bytes_written} (dur={dur:.2f}s)\n")
    safe_flush()

    # Cálculo de métricas RMS
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
    return bytes_written, rms

def correr_reproduccion_5s():
    sys.stdout.write("[STEP 7] Entrando correr_reproduccion_5s\n")
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
    time.sleep(5.0)   # Esperar los 5 segundos completos

    if oled:
        oled.fill(0)
        oled.rect(0, 0, 128, 64, 1)
        oled.text(" Grabacion", 20, 12, 1)
        oled.text(" completada", 18, 26, 1)
        oled.text("Microfono OK", 14, 46, 1)
        oled.show()
        time.sleep(1.8)

def animacion_oled_completa():
    """Prueba OLED rediseñada: Osciloscopio ➔ Ecualizador ➔ ASISTENTE FIN. ➔ Icono Robot ➔ Checkmark ✔"""
    if not oled: return

    # 1. Animación Osciloscopio (8 frames)
    for frame in range(8):
        oled.fill(0)
        oled.rect(0, 0, 128, 64, 1)
        offset = frame * 8
        for x in range(1, 127):
            y1 = int(32 + 20 * math.sin(2 * math.pi * (x + offset) / 36))
            y2 = int(32 + 20 * math.sin(2 * math.pi * (x + 1 + offset) / 36))
            oled.line(x, y1, x + 1, y2, 1)
        oled.show()
        time.sleep(0.06)

    # 2. Animación Barras de Ecualizador Spectrum (8 frames)
    for frame in range(8):
        oled.fill(0)
        oled.rect(0, 0, 128, 64, 1)
        for b in range(10):
            h_bar = int(10 + 35 * math.abs(math.sin((frame + b) * 0.7)))
            oled.fill_rect(10 + b * 11, 56 - h_bar, 8, h_bar, 1)
        oled.text("AUDIO SPECTRUM", 8, 4, 1)
        oled.show()
        time.sleep(0.08)

    # 3. Nombre del proyecto
    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)
    oled.text("  ASISTENTE", 20, 18, 1)
    oled.text("  FINANCIERO", 16, 36, 1)
    oled.show()
    time.sleep(1.0)

    # 4. Icono / Logotipo del Asistente
    dibujar_icono_robot()
    time.sleep(1.2)

    # 5. Checkmark ✔ PRUEBA FINALIZADA
    dibujar_checkmark_exito()
    time.sleep(1.8)

def mostrar_idle():
    if not oled: return
    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)
    oled.text("ASISTENTE FIN.", 8, 15, 1)
    oled.text("Listo en PC", 18, 35, 1)
    oled.show()

# ==============================================================================
# BUCLE PRINCIPAL (CON GARBAGE COLLECTION HEAP)
# ==============================================================================
sys.stdout.write("[ESP32-S3] READY (v2.1 Advanced Tests & GC)\n")
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

        elif cmd in ("OLED_TEST", "OLED_ANIM"):
            gc.collect()
            sys.stdout.write("[OLED_ANIM] Ejecutando secuencia animada completa...\n")
            safe_flush()
            animacion_oled_completa()
            mostrar_idle()
            gc.collect()
            sys.stdout.write("OLED_TEST_OK\n")
            safe_flush()

        elif cmd == "AUDIO_TEST":
            gc.collect()
            sys.stdout.write("[AUDIO_TEST] Reproduciendo melodía musical demostrativa 4s...\n")
            safe_flush()
            reproducir_melodia_reconocible()
            mostrar_idle()
            gc.collect()
            sys.stdout.write("AUDIO_TEST_OK\n")
            safe_flush()

        elif cmd in ("MIC_TEST", "MIC_START"):
            gc.collect()
            sys.stdout.write("[STEP 1] Entrando MIC_TEST (5s guiado)\n")
            safe_flush()
            if not audio_in or not audio_out:
                sys.stdout.write("MIC_TEST_FAIL: I2S is None\n")
                safe_flush()
                continue
            try:
                correr_grabacion_guiada_5s()
                correr_reproduccion_5s()
                mostrar_idle()
                gc.collect()
                sys.stdout.write("[STEP 10] Enviando MIC_TEST_OK\n")
                safe_flush()
                sys.stdout.write("MIC_TEST_OK\n")
                safe_flush()
            except Exception as ex:
                gc.collect()
                sys.stdout.write(f"MIC_TEST_FAIL: {ex}\n")
                safe_flush()

        elif cmd.startswith("AUDIO_PLAY:"):
            gc.collect()
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

            play_buf = bytearray(total_bytes)
            pos = 0
            while pos < total_bytes:
                line_b64 = sys.stdin.readline()
                if not line_b64:
                    continue
                s = line_b64.strip()
                if s == "STOP" or s == "AUDIO_PLAY_END":
                    break
                try:
                    chunk = ubinascii.a2b_base64(s)
                    end = min(pos + len(chunk), total_bytes)
                    play_buf[pos:end] = chunk[:end - pos]
                    pos = end
                except Exception as ex_b64:
                    sys.stdout.write(f"[AUDIO_PLAY ERR] {ex_b64}\n")
                    safe_flush()

            if audio_out and pos > 0:
                audio_out.write(play_buf[:pos])
                dur_wait = pos / (SAMPLE_RATE * 2) + 0.3
                time.sleep(dur_wait)

            mostrar_idle()
            gc.collect()
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
        gc.collect()
        sys.stdout.write(f"[MAIN ERR] {err}\n")
        safe_flush()
