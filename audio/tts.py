import re
import threading
import pyttsx3

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
    Sintetiza el texto usando la voz en español de México (Microsoft Sabina) de forma fluida.
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
                engine = pyttsx3.init()
                voces = engine.getProperty('voices')
                
                # Buscar específicamente la voz en español Sabina (México) o cualquier voz en español
                voz_seleccionada = None
                for voz in voces:
                    nombre_lower = voz.name.lower()
                    id_lower = voz.id.lower()
                    if "sabina" in nombre_lower or "es-mx" in id_lower or "spanish (mexico)" in nombre_lower:
                        voz_seleccionada = voz.id
                        break
                    elif "spanish" in nombre_lower or "es-" in id_lower or "es_" in id_lower:
                        voz_seleccionada = voz.id

                if voz_seleccionada:
                    engine.setProperty('voice', voz_seleccionada)
                
                engine.setProperty('rate', 155)  # Velocidad fluida y natural
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
