import pyttsx3
import time

# Inicializamos el motor globalmente para no recrearlo cada vez
engine = pyttsx3.init()

# Configuración básica (intentar buscar voz en español)
voces = engine.getProperty('voices')
for voz in voces:
    if "spanish" in voz.name.lower() or "es" in voz.languages:
        engine.setProperty('voice', voz.id)
        break
engine.setProperty('rate', 150) # Velocidad de habla

def hablar(texto):
    """
    Toma una cadena de texto y la reproduce a través del circuito físico o los altavoces de la PC.
    """
    try:
        from comunicacion_esp32 import esp32_comm
        if esp32_comm.conectado:
            # Notificar al ESP32-S3 que entre en estado de respuesta visual en OLED y emita el tono de confirmación en la bocina física MAX98357A
            esp32_comm.enviar_comando_oled("RESPONDIENDO", texto[:12])
            esp32_comm.ejecutar_test_audio()
    except Exception:
        pass

    # Reproducción continua del sintetizador offline
    engine.say(texto)
    engine.runAndWait()

    try:
        from comunicacion_esp32 import esp32_comm
        if esp32_comm.conectado:
            esp32_comm.enviar_comando_oled("IDLE")
    except Exception:
        pass
