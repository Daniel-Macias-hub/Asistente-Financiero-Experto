import re
import threading

def limpiar_texto_para_tts(texto: str) -> str:
    """
    Limpia el texto eliminando símbolos markdown (*, #, _, ~, ─, •) y emojis
    para que la voz sintética no lea 'asterisco asterisco' ni caracteres raros.
    """
    if not texto:
        return ""
    
    # 1. Eliminar formato markdown
    t = re.sub(r'\*+', '', texto)
    t = re.sub(r'#+', '', t)
    t = re.sub(r'_+', '', t)
    t = re.sub(r'~+', '', t)
    t = re.sub(r'`+', '', t)
    t = re.sub(r'[\─\─\─\─\─\─]+', '', t)
    t = re.sub(r'•', '', t)
    
    # 2. Eliminar emojis
    t = re.sub(r'[\U00010000-\U0010ffff]', '', t)
    t = re.sub(r'[📊💰🇲🇽📅💵🏦📖🔍🎙️🤖⚠️❌✓⚙🔴🔊💡📷⚡]', '', t)
    
    # 3. Limpiar espacios múltiples
    t = re.sub(r'\s+', ' ', t).strip()
    return t

_tts_lock = threading.Lock()

def detener_habla():
    """Detiene la reproducción de voz actual."""
    try:
        from comunicacion_esp32 import esp32_comm
        if esp32_comm.conectado:
            esp32_comm.enviar_comando_oled("IDLE")
    except Exception:
        pass

def hablar(texto: str):
    """
    Sintetiza el texto usando pyttsx3 en un hilo dedicado de forma segura
    sin bloquear la interfaz ni otras consultas.
    """
    texto_limpio = limpiar_texto_para_tts(texto)
    if not texto_limpio:
        return

    def _run_tts():
        with _tts_lock:
            try:
                from comunicacion_esp32 import esp32_comm
                if esp32_comm.conectado:
                    esp32_comm.enviar_comando_oled("RESPONDIENDO", texto_limpio[:12])
            except Exception:
                pass

            try:
                import pyttsx3
                engine = pyttsx3.init()
                voces = engine.getProperty('voices')
                for voz in voces:
                    if any(k in voz.name.lower() for k in ["spanish", "es", "sabina", "helena", "raul", "pablo"]):
                        engine.setProperty('voice', voz.id)
                        break
                engine.setProperty('rate', 165)
                engine.setProperty('volume', 1.0)
                engine.say(texto_limpio)
                engine.runAndWait()
            except Exception as e:
                print(f"[TTS WARNING] {e}")
            finally:
                try:
                    from comunicacion_esp32 import esp32_comm
                    if esp32_comm.conectado:
                        esp32_comm.enviar_comando_oled("IDLE")
                except Exception:
                    pass

    threading.Thread(target=_run_tts, daemon=True).start()
