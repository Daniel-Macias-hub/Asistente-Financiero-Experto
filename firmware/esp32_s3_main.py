# ==============================================================================
# FIRMWARE DEFINITIVO UNIFICADO ESP32-S3 (PCB MRD085A / Kit OKYN-G5806)
# Bucle Continuo con Animación OLED de Osciloscopio + Pre-Asignación Estática (64KB RAM)
# Comandos: PING, STATE, OLED_TEST, AUDIO_TEST, MIC_START
# ==============================================================================
import machine
from machine import Pin, I2S
import ssd1306
import time
import struct
import sys
import math
import uselect
import gc

def safe_flush():
    """Función de flush seguro compatible con MicroPython."""
    if hasattr(sys.stdout, 'flush'):
        try:
            sys.stdout.flush()
        except Exception:
            pass

# ------------------------------------------------------------------------------
# Configuración de Pines (PCB MRD085A)
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
RECORD_SECS = 2
BUFFER_SIZE_16BIT = SAMPLE_RATE * 2 * RECORD_SECS  # 64,000 bytes (Ultra ligero)

# Pre-asignación Estática de Búfer Global en RAM al arrancar el módulo
gc.collect()
AUDIO_RAM = bytearray(BUFFER_SIZE_16BIT)
READ_BUF  = bytearray(512)
TEMP_BUF  = bytearray(256)
TONE_BUF  = bytearray(SAMPLE_RATE * 2)

# ------------------------------------------------------------------------------
# Inicialización OLED SSD1306
# ------------------------------------------------------------------------------
oled = None
try:
    i2c = machine.SoftI2C(scl=Pin(OLED_SCL), sda=Pin(OLED_SDA))
    oled = ssd1306.SSD1306_I2C(128, 64, i2c)
except Exception as e:
    sys.stdout.write(f"[OLED ERR] {e}\n")

# Apagar NeoPixels integrados
try:
    import neopixel
    for p in [48, 38, 8]:
        np = neopixel.NeoPixel(Pin(p), 1)
        np[0] = (0, 0, 0)
        np.write()
except Exception:
    pass

# ------------------------------------------------------------------------------
# Canales Audio I2S (0 RX: Mic / 1 TX: Bocina)
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

# ------------------------------------------------------------------------------
# Funciones de Animación OLED estilo Osciloscopio
# ------------------------------------------------------------------------------
def animacion_osciloscopio(titulo, frame, amplitud=14, frec=0.18):
    if not oled: return
    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)
    oled.text(titulo, 8, 6, 1)
    
    # Línea central de referencia
    for x in range(4, 124, 8):
        oled.pixel(x, 40, 1)
        
    # Trazo de la onda senoidal continua
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
# Pruebas de Hardware Físicas
# ------------------------------------------------------------------------------
def ejecutar_test_oled_secuencia():
    sys.stdout.write("[TEST] OLED Secuencia...\n")
    safe_flush()
    estados = [
        ("INICIANDO", animacion_iniciando),
        ("ESCUCHANDO", animacion_escuchando),
        ("PROCESANDO", animacion_procesando),
        ("RESPONDIENDO", animacion_respondiendo),
        ("ERROR", lambda p: animacion_error("TEST ERROR"))
    ]
    for nombre, func in estados:
        t_start = time.time()
        f = 0
        while time.time() - t_start < 1.0:
            func(f)
            f += 1
            time.sleep(0.05)
    mostrar_idle()
    sys.stdout.write("OLED_TEST_OK\n")
    safe_flush()

def reproducir_tono_prueba_audio():
    sys.stdout.write("[TEST] Reproduciendo audio...\n")
    safe_flush()
    if not audio_out:
        sys.stdout.write("AUDIO_TEST_ERR\n")
        safe_flush()
        return

    freq = 440
    amplitude = 12000
    for i in range(SAMPLE_RATE):
        sample = int(amplitude * math.sin(2 * math.pi * freq * (i / SAMPLE_RATE)))
        struct.pack_into("<h", TONE_BUF, i * 2, sample)
    
    audio_out.write(TONE_BUF)
    time.sleep(0.1)
    sys.stdout.write("AUDIO_TEST_OK\n")
    safe_flush()

def grabar_y_transmitir_mic():
    if not audio_in:
        sys.stdout.write("MIC_DATA:0\n")
        safe_flush()
        return

    gc.collect()
    
    # Limpiar búfer previo de la entrada I2S
    for _ in range(5):
        audio_in.readinto(TEMP_BUF)

    bytes_written = 0
    while bytes_written < BUFFER_SIZE_16BIT:
        num_read = audio_in.readinto(READ_BUF)
        if num_read > 0:
            num_samples = num_read // 4
            for s_idx in range(num_samples):
                if bytes_written >= BUFFER_SIZE_16BIT:
                    break
                val_32 = struct.unpack("<i", READ_BUF[s_idx*4 : (s_idx+1)*4])[0]
                val_16 = val_32 >> 16
                struct.pack_into("<h", AUDIO_RAM, bytes_written, val_16)
                bytes_written += 2
                
    sys.stdout.write(f"MIC_DATA:{len(AUDIO_RAM)}\n")
    safe_flush()
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout.buffer.write(AUDIO_RAM)
    else:
        sys.stdout.write(AUDIO_RAM)
    safe_flush()
    gc.collect()

# ------------------------------------------------------------------------------
# Bucle Principal de Control Serial e Interrupción Inmediata
# ------------------------------------------------------------------------------
def main():
    poll_obj = uselect.poll()
    poll_obj.register(sys.stdin, uselect.POLLIN)

    estado_actual = "IDLE"
    frame_counter = 0
    mostrar_idle()
    
    sys.stdout.write("[ESP32-S3] READY\n")
    safe_flush()

    while True:
        try:
            events = poll_obj.poll(40)
            for obj, flag in events:
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
