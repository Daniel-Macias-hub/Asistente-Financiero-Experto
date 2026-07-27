import pyttsx3
import time

# Inicializamos el motor globalmente para no recrearlo cada vez
engine = pyttsx3.init()

# Configuración básica (buscar voz en español)
voces = engine.getProperty('voices')
for voz in voces:
    if "spanish" in voz.name.lower() or "es" in voz.languages:
        engine.setProperty('voice', voz.id)
        break
engine.setProperty('rate', 150) # Velocidad de habla

def hablar(texto):
    """
    Sintetiza la respuesta en voz en español fluida y actualiza la animación del osciloscopio en el OLED del ESP32-S3.
    """
    try:
        from comunicacion_esp32 import esp32_comm
        if esp32_comm.conectado:
            esp32_comm.enviar_comando_oled("RESPONDIENDO", texto[:12])
    except Exception:
        pass

    # Reproducción en voz alta hablada
    try:
        engine.say(texto)
        engine.runAndWait()
    except Exception as e:
        print(f"[TTS ERR] {e}")

    try:
        from comunicacion_esp32 import esp32_comm
        if esp32_comm.conectado:
            esp32_comm.enviar_comando_oled("IDLE")
    except Exception:
        pass
