import machine
from machine import Pin, I2S
import ssd1306
import time
import struct

# ==============================================================================
# CONFIGURACIÓN DE PINES
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
BUFFER_SIZE_16BIT = SAMPLE_RATE * 2 * RECORD_SECS

# ==============================================================================
# INICIALIZACIÓN DE LA PANTALLA OLED
# ==============================================================================
print("Iniciando OLED...")
oled = None
try:
    i2c = machine.SoftI2C(scl=Pin(OLED_SCL), sda=Pin(OLED_SDA))
    oled = ssd1306.SSD1306_I2C(128, 64, i2c)
    oled.fill(0)
    oled.rect(0, 0, 128, 64, 1)
    oled.text("ECO GRABADORA", 12, 20, 1)
    oled.text("Estabilizando...", 8, 40, 1)
    oled.show()
except Exception as e:
    print("Error OLED:", e)

# Apagar LED blanco
try:
    import neopixel
    for p in [48, 38, 8]:
        np = neopixel.NeoPixel(Pin(p), 1)
        np[0] = (0, 0, 0)
        np.write()
except Exception:
    pass

# ==============================================================================
# INICIALIZACIÓN ÚNICA DE PUERTOS I2S (Evita bloqueos de hardware)
# ==============================================================================
print("Inicializando canales de audio I2S (Única vez)...")

# Inicializar Micrófono (I2S 0 RX)
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

# Inicializar Bocina (I2S 1 TX)
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
print("Canales de audio listos.")

# ==============================================================================
# BUFER Y LÓGICA DE GRABACIÓN
# ==============================================================================
audio_ram = bytearray(BUFFER_SIZE_16BIT)
read_buf = bytearray(512)

def correr_grabacion():
    # Limpiar búfer
    for i in range(len(audio_ram)):
        audio_ram[i] = 0

    print("Grabando en 3 segundos...")
    for countdown in range(3, 0, -1):
        if oled:
            oled.fill(0)
            oled.rect(0, 0, 128, 64, 1)
            oled.text("GRABANDO EN...", 12, 15, 1)
            oled.text(f"      {countdown}", 12, 35, 1)
            oled.show()
        print(f"  {countdown}...")
        time.sleep(1)

    if oled:
        oled.fill(0)
        oled.rect(0, 0, 128, 64, 1)
        oled.text(" 🔴 GRABANDO ", 15, 15, 1)
        oled.text("Habla ahora!", 16, 38, 1)
        oled.show()
    print("🔴 ¡GRABANDO AHORA!")
    
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
                
    print("Grabación finalizada.")

def correr_reproduccion():
    print("🟢 ¡REPRODUCIENDO!")
    if oled:
        oled.fill(0)
        oled.rect(0, 0, 128, 64, 1)
        oled.text(" 🟢 REPRODUCIENDO ", 5, 15, 1)
        oled.text("Escucha la bocina", 4, 38, 1)
        oled.show()
        
    audio_out.write(audio_ram)
    time.sleep(0.1)
    print("Reproducción finalizada.")

# ==============================================================================
# BUCLE PRINCIPAL DEL TEST
# ==============================================================================
try:
    while True:
        # 1. Grabar en RAM
        correr_grabacion()
        
        # 2. Tocar por bocina
        correr_reproduccion()
        
        # Esperar 2 segundos antes de repetir el ciclo
        if oled:
            oled.fill(0)
            oled.rect(0, 0, 128, 64, 1)
            oled.text("Listo para repetir", 4, 25, 1)
            oled.show()
        print("\nCiclo completado. Esperando 2 segundos para repetir...\n")
        time.sleep(2)
        
except KeyboardInterrupt:
    print("\nTest detenido por el usuario.")
    # Intentar liberar recursos al salir con Ctrl+C
    try:
        audio_in.deinit()
        audio_out.deinit()
    except Exception:
        pass
    if oled:
        oled.fill(0)
        oled.text("Test detenido", 10, 25, 1)
        oled.show()
