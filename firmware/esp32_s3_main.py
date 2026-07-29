# ==============================================================================
# FIRMWARE ESP32-S3 — PRODUCCIÓN ESTABLE (0 MEMORY ERROR)
# Hardware: PCB MRD085A / Kit OKYN-G5806 (ESP32-S3 N16R8)
# Tono/Melodía con buffer estático de 1KB, Micrófono (20 bloques x 4KB = 80KB), OLED animado
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
NUM_CHUNKS        = 20
CHUNK_SIZE        = 4096
# 20 * 4096 = 81 920 bytes (2.56s a 16kHz 16-bit mono -> cabe perfecto en RAM de MicroPython)

# ==============================================================================
# INICIALIZACIÓN PANTALLA OLED
# ==============================================================================
oled = None
try:
    i2c = machine.SoftI2C(scl=Pin(OLED_SCL), sda=Pin(OLED_SDA), freq=100000)
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

audio_ram_chunks = None
read_buf = bytearray(512)

# ==============================================================================
# DIBUJO EN OLED
# ==============================================================================
def dibujar_icono_robot():
    if not oled: return
    try:
        oled.fill(0)
        oled.rect(48, 12, 32, 26, 1)
        oled.fill_rect(54, 20, 6, 6, 1)
        oled.fill_rect(68, 20, 6, 6, 1)
        oled.line(64, 4, 64, 12, 1)
        oled.fill_rect(62, 2, 5, 3, 1)
        oled.line(56, 32, 72, 32, 1)
        oled.rect(42, 40, 44, 20, 1)
        oled.text("AI BOT", 48, 46, 1)
        oled.show()
    except Exception:
        pass

def dibujar_checkmark_exito():
    if not oled: return
    try:
        oled.fill(0)
        oled.rect(0, 0, 128, 64, 1)
        for w in range(-2, 3):
            oled.line(36 + w, 32, 52 + w, 48, 1)
        for w in range(-2, 3):
            oled.line(52 + w, 48, 92 + w, 16, 1)
        oled.text("PRUEBA FINALIZADA", 4, 52, 1)
        oled.show()
    except Exception:
        pass

# ==============================================================================
# FUNCIONES DE AUDIO (SIN MEMORY ERROR)
# ==============================================================================
def reproducir_melodia_reconocible():
    """Melodía armónica demostrativa usando un búfer estático de 1KB (0 MemoryError)."""
    sys.stdout.write("[AUDIO_TEST] Generando melodía musical demostrativa de 4s...\n")
    safe_flush()
    if not audio_out:
        raise RuntimeError("audio_out is None")

    if oled:
        try:
            oled.fill(0)
            oled.rect(0, 0, 128, 64, 1)
            oled.text("  BOCINA TEST", 14, 15, 1)
            oled.text("  REPRODUCIENDO", 10, 32, 1)
            oled.text("  MELODIA 4s", 20, 48, 1)
            oled.show()
        except Exception:
            pass

    notas = [
        (261.6, 220), (261.6, 220), (293.7, 400), (261.6, 400), (349.2, 400), (329.6, 600),
        (261.6, 220), (261.6, 220), (293.7, 400), (261.6, 400), (392.0, 400), (349.2, 600)
    ]
    AMP = 7000
    buf_slice = bytearray(1024)

    for freq, dur_ms in notas:
        total_samples = int(SAMPLE_RATE * (dur_ms / 1000.0))
        s_written = 0
        while s_written < total_samples:
            batch = min(512, total_samples - s_written)
            for i in range(batch):
                idx_g = s_written + i
                val = AMP * math.sin(2 * math.pi * freq * idx_g / SAMPLE_RATE)
                if idx_g < 240:
                    val *= (idx_g / 240)
                elif idx_g > total_samples - 240:
                    val *= ((total_samples - idx_g) / 240)
                struct.pack_into("<h", buf_slice, i * 2, int(val))
            audio_out.write(buf_slice[:batch * 2])
            s_written += batch
        time.sleep(0.02)

    time.sleep(0.3)

def correr_grabacion_guiada_5s():
    global audio_ram_chunks
    gc.collect()
    sys.stdout.write("[MIC_TEST] Reservando 20 bloques de 4KB (80KB)... \n")
    safe_flush()

    audio_ram_chunks = [bytearray(CHUNK_SIZE) for _ in range(NUM_CHUNKS)]

    if not audio_in:
        raise RuntimeError("audio_in is None")

    if oled:
        try:
            oled.fill(0)
            oled.rect(0, 0, 128, 64, 1)
            oled.text("Prueba de", 28, 15, 1)
            oled.text("microfono", 28, 35, 1)
            oled.show()
        except Exception:
            pass
        time.sleep(0.8)

    for countdown in range(3, 0, -1):
        if oled:
            try:
                oled.fill(0)
                oled.rect(0, 0, 128, 64, 1)
                oled.text("Iniciando en:", 14, 15, 1)
                oled.text(f"      {countdown}", 12, 38, 1)
                oled.show()
            except Exception:
                pass
        time.sleep(0.6)

    if oled:
        try:
            oled.fill(0)
            oled.rect(0, 0, 128, 64, 1)
            oled.text("   ¡YA!", 36, 25, 1)
            oled.show()
        except Exception:
            pass
        time.sleep(0.3)

    temp = bytearray(256)
    for _ in range(5):
        audio_in.readinto(temp)

    bytes_written = 0
    total_target = NUM_CHUNKS * CHUNK_SIZE
    t0 = time.time()
    last_vumeter_update = 0

    chunk_idx = 0
    chunk_off = 0

    while bytes_written < total_target:
        num_read = audio_in.readinto(read_buf)
        if num_read > 0:
            ns = num_read // 4
            chunk_max = 0
            for s in range(ns):
                if bytes_written >= total_target:
                    break
                v32 = struct.unpack("<i", read_buf[s*4:(s+1)*4])[0]
                v16 = max(-32768, min(32767, v32 >> 12))
                
                struct.pack_into("<h", audio_ram_chunks[chunk_idx], chunk_off, v16)
                bytes_written += 2
                chunk_off += 2
                if chunk_off >= CHUNK_SIZE:
                    chunk_idx += 1
                    chunk_off = 0

                abs_v = abs(v16)
                if abs_v > chunk_max: chunk_max = abs_v

            t_now = time.time()
            if oled and (t_now - last_vumeter_update > 0.10):
                last_vumeter_update = t_now
                seg_act = int(t_now - t0) + 1
                level_ratio = min(1.0, chunk_max / 16000.0)
                bar_w = int(level_ratio * 104)

                try:
                    oled.fill(0)
                    oled.rect(0, 0, 128, 64, 1)
                    oled.text(f" GRABANDO ({seg_act}s/3s)", 8, 10, 1)
                    oled.rect(12, 30, 104, 14, 1)
                    if bar_w > 0:
                        oled.fill_rect(12, 30, bar_w, 14, 1)
                    oled.show()
                except Exception:
                    pass

    dur = time.time() - t0
    sys.stdout.write(f"[STEP 5] bytes_written={bytes_written} (dur={dur:.2f}s)\n")
    safe_flush()

    num_s = bytes_written // 2
    total_sq = 0
    min_v, max_v = 32767, -32768
    samples16 = []

    s_count = 0
    for c in range(NUM_CHUNKS):
        if s_count >= num_s: break
        for off in range(0, CHUNK_SIZE, 2):
            sv = struct.unpack_from("<h", audio_ram_chunks[c], off)[0]
            if s_count < 16: samples16.append(sv)
            if sv < min_v: min_v = sv
            if sv > max_v: max_v = sv
            total_sq += sv * sv
            s_count += 1

    rms = math.sqrt(total_sq / max(1, num_s))
    sys.stdout.write(f"[STEP 5.1] Muestras_16={samples16}, Min={min_v}, Max={max_v}, RMS={rms:.2f}\n")
    safe_flush()
    return bytes_written, rms

def correr_reproduccion_5s():
    sys.stdout.write("[STEP 7] Entrando correr_reproduccion_5s\n")
    safe_flush()
    if not audio_out or not audio_ram_chunks:
        raise RuntimeError("audio_out is None or audio_ram_chunks is None")

    if oled:
        try:
            oled.fill(0)
            oled.rect(0, 0, 128, 64, 1)
            oled.text(" REPRODUCIENDO", 8, 15, 1)
            oled.text("Escucha bocina", 10, 38, 1)
            oled.show()
        except Exception:
            pass

    for chunk in audio_ram_chunks:
        audio_out.write(chunk)

    sys.stdout.write("[STEP 8] audio_out.write por bloques completado\n")
    safe_flush()
    time.sleep(0.3)

    if oled:
        try:
            oled.fill(0)
            oled.rect(0, 0, 128, 64, 1)
            oled.text(" Grabacion", 20, 12, 1)
            oled.text(" completada", 18, 26, 1)
            oled.text("Microfono OK", 14, 46, 1)
            oled.show()
        except Exception:
            pass
        time.sleep(1.0)

def animacion_oled_completa():
    if not oled: return
    try:
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

        for frame in range(8):
            oled.fill(0)
            oled.rect(0, 0, 128, 64, 1)
            for b in range(10):
                h_bar = int(10 + 35 * math.abs(math.sin((frame + b) * 0.7)))
                oled.fill_rect(10 + b * 11, 56 - h_bar, 8, h_bar, 1)
            oled.text("AUDIO SPECTRUM", 8, 4, 1)
            oled.show()
            time.sleep(0.08)

        oled.fill(0)
        oled.rect(0, 0, 128, 64, 1)
        oled.text("  ASISTENTE", 20, 18, 1)
        oled.text("  FINANCIERO", 16, 36, 1)
        oled.show()
        time.sleep(1.0)

        dibujar_icono_robot()
        time.sleep(1.0)

        dibujar_checkmark_exito()
        time.sleep(1.2)
    except Exception:
        pass

def mostrar_idle():
    if not oled: return
    try:
        oled.fill(0)
        oled.rect(0, 0, 128, 64, 1)
        oled.text("ASISTENTE FIN.", 8, 15, 1)
        oled.text("Listo en PC", 18, 35, 1)
        oled.show()
    except Exception:
        pass

# ==============================================================================
# BUCLE PRINCIPAL (0 MEMORY ERROR)
# ==============================================================================
sys.stdout.write("[BOOT] ESP32-S3 arrancando. Iniciando main.py...\n")
safe_flush()
sys.stdout.write("[ESP32-S3] READY (v2.3 Ultra Stable RAM)\n")
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
                try:
                    oled.fill(0)
                    oled.rect(0, 0, 128, 64, 1)
                    oled.text(" RESPONDIENDO", 10, 20, 1)
                    oled.text(" Voz IA", 34, 40, 1)
                    oled.show()
                except Exception:
                    pass

            sys.stdout.write("AUDIO_PLAY_READY\n")
            safe_flush()

            # Fragmentación en bloques estáticos de 2KB para 0 MemoryError
            play_chunks = [bytearray(min(2048, total_bytes - i)) for i in range(0, total_bytes, 2048)]
            c_idx = 0
            c_off = 0

            while c_idx < len(play_chunks):
                line_b64 = sys.stdin.readline()
                if not line_b64:
                    continue
                s = line_b64.strip()
                if s == "STOP" or s == "AUDIO_PLAY_END":
                    break
                try:
                    chunk = ubinascii.a2b_base64(s)
                    target = play_chunks[c_idx]
                    rem = len(target) - c_off
                    if len(chunk) <= rem:
                        target[c_off:c_off+len(chunk)] = chunk
                        c_off += len(chunk)
                    else:
                        target[c_off:] = chunk[:rem]
                        c_idx += 1
                        c_off = len(chunk) - rem
                        if c_idx < len(play_chunks):
                            play_chunks[c_idx][:c_off] = chunk[rem:]
                    if c_off >= len(play_chunks[c_idx]):
                        c_idx += 1
                        c_off = 0
                except Exception as ex_b64:
                    sys.stdout.write(f"[AUDIO_PLAY ERR] {ex_b64}\n")
                    safe_flush()

            if audio_out:
                for p_chunk in play_chunks:
                    audio_out.write(p_chunk)
                dur_wait = total_bytes / (SAMPLE_RATE * 2) + 0.3
                time.sleep(dur_wait)

            mostrar_idle()
            gc.collect()
            sys.stdout.write("AUDIO_PLAY_OK\n")
            safe_flush()

        elif cmd.startswith("STATE:"):
            partes = cmd.split(":")
            st = partes[1].upper() if len(partes) >= 2 else "IDLE"
            if oled:
                try:
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
                except Exception:
                    pass
            sys.stdout.write(f"STATE_ACK:{st}\n")
            safe_flush()

    except Exception as err:
        gc.collect()
        sys.stdout.write(f"[MAIN ERR] {err}\n")
        safe_flush()
