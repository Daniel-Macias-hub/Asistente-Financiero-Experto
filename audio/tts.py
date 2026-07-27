import re
import pyttsx3
import threading

# Inicializamos el motor globalmente
engine = pyttsx3.init()

# Configuración de voz en español
voces = engine.getProperty('voices')
for voz in voces:
    if "spanish" in voz.name.lower() or "es" in voz.languages or "sabina" in voz.name.lower() or "helena" in voz.name.lower():
        engine.setProperty('voice', voz.id)
        break

engine.setProperty('rate', 160)  # Velocidad de habla natural fluida
engine.setProperty('volume', 1.0) # Volumen máximo

reproduciendo = False

def limpiar_texto_para_tts(texto: str) -> str:
    """
    Limpia el texto eliminando símbolos markdown (*, #, _, ~, ─, •) y emojis
    para que la voz sintética no lea 'asterisco asterisco' ni caracteres raros.
    """
    if not texto:
        return ""
    
    # 1. Eliminar formato markdown (**bold**, *italic*, # headers, etc.)
    t = re.sub(r'\*+', '', texto)
    t = re.sub(r'#+', '', t)
    t = re.sub(r'_+', '', t)
    t = re.sub(r'~+', '', t)
    t = re.sub(r'`+', '', t)
    t = re.sub(r'[\─\─\─\─\─\─]+', '', t)
    t = re.sub(r'•', '', t)
    
    # 2. Eliminar emojis comunes de la interfaz
    t = re.sub(r'[\U00010000-\U0010ffff]', '', t)
    t = re.sub(r'[📊💰🇲🇽📅💵🏦📖🔍🎙️🤖⚠️❌✓⚙🔴🔊💡📷⚡]', '', t)
    
    # 3. Limpiar espacios múltiples y saltos innecesarios
    t = re.sub(r'\s+', ' ', t).strip()
    return t

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
    Sintetiza la respuesta en voz fluida y natural en español sin pronunciar 'asteriscos'.
    """
    global reproduciendo
    reproduciendo = True

    texto_limpio = limpiar_texto_para_tts(texto)
    if not texto_limpio:
        return

    try:
        from comunicacion_esp32 import esp32_comm
        if esp32_comm.conectado:
            esp32_comm.enviar_comando_oled("RESPONDIENDO", texto_limpio[:12])
    except Exception:
        pass

    try:
        if reproduciendo:
            engine.say(texto_limpio)
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
