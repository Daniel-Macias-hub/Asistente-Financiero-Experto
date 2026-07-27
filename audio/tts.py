import pyttsx3
import time
import threading

# Inicializamos el motor globalmente
engine = pyttsx3.init()

# Configuración básica (voz en español)
voces = engine.getProperty('voices')
for voz in voces:
    if "spanish" in voz.name.lower() or "es" in voz.languages:
        engine.setProperty('voice', voz.id)
        break
engine.setProperty('rate', 150) # Velocidad de habla

reproduciendo = False

def detener_habla():
    """Detiene inmediatamente la reproducción de voz del asistente."""
    global reproduciendo
    reproduciendo = False
    try:
        engine.stop()
    except Exception:
        pass
    try:
        from comunicacion_esp32 import esp32_comm
        if esp32_comm.conectado:
            esp32_comm.enviar_comando_oled("IDLE")
    except Exception:
        pass

def hablar(texto):
    """
    Sintetiza la respuesta en voz fluida en español y conmuta la animación OLED.
    """
    global reproduciendo
    reproduciendo = True

    try:
        from comunicacion_esp32 import esp32_comm
        if esp32_comm.conectado:
            esp32_comm.enviar_comando_oled("RESPONDIENDO", texto[:12])
    except Exception:
        pass

    try:
        if reproduciendo:
            engine.say(texto)
            engine.runAndWait()
    except Exception as e:
        print(f"[TTS ERR] {e}")
    finally:
        reproduciendo = False
        try:
            from comunicacion_esp32 import esp32_comm
            if esp32_comm.conectado:
                esp32_comm.enviar_comando_oled("IDLE")
        except Exception:
            pass
