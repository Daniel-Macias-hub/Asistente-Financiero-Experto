import re
import threading
import os
import wave
import numpy as np
import pyttsx3

def limpiar_texto_para_tts(texto: str) -> str:
    """
    Limpia el texto eliminando símbolos markdown (*, #, _, ~, ─, •) y emojis
    para que la voz sintética no lea 'asterisco asterisco' ni caracteres raros.
    """
    if not texto:
        return ""
    
    t = re.sub(r'\*+', '', texto)
    t = re.sub(r'#+', '', t)
    t = re.sub(r'_+', '', t)
    t = re.sub(r'~+', '', t)
    t = re.sub(r'`+', '', t)
    t = re.sub(r'[\─\─\─\─\─\─]+', '', t)
    t = re.sub(r'•', '', t)
    
    t = re.sub(r'[\U00010000-\U0010ffff]', '', t)
    t = re.sub(r'[📊💰🇲🇽📅💵🏦📖🔍🎙️🤖⚠️❌✓⚙🔴🔊💡📷⚡]', '', t)
    
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def _convertir_wav_a_pcm_16k_mono(wav_path: str) -> bytes:
    """Lee un archivo WAV y lo remuestra a PCM 16kHz Mono 16-bit."""
    try:
        with wave.open(wav_path, 'rb') as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            raw_bytes = wf.readframes(n_frames)

        if sampwidth == 2:
            audio = np.frombuffer(raw_bytes, dtype=np.int16)
        else:
            audio = np.frombuffer(raw_bytes, dtype=np.int16)

        if n_channels > 1:
            audio = audio.reshape(-1, n_channels).mean(axis=1).astype(np.int16)

        if framerate != 16000 and len(audio) > 0:
            new_len = int(len(audio) * 16000 / framerate)
            audio = np.interp(
                np.linspace(0, len(audio), new_len, endpoint=False),
                np.arange(len(audio)),
                audio
            ).astype(np.int16)

        return audio.tobytes()
    except Exception as e:
        print(f"[WAV CONVERT ERR] {e}")
        return b""

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
    Sintetiza el texto y transmite el audio PCM directamente a la bocina MAX98357A del circuito.
    """
    texto_limpio = limpiar_texto_para_tts(texto)
    if not texto_limpio:
        return

    def _run_tts():
        with _tts_lock:
            from comunicacion_esp32 import esp32_comm
            temp_wav = f"temp_speech_{threading.get_ident()}.wav"
            
            try:
                engine = pyttsx3.init()
                voces = engine.getProperty('voices')
                
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
                
                engine.setProperty('rate', 155)
                engine.setProperty('volume', 1.0)

                # Si el circuito está conectado por USB, renderizar WAV y enviar por I2S a la bocina
                if esp32_comm.conectado:
                    engine.save_to_file(texto_limpio, temp_wav)
                    engine.runAndWait()
                    
                    if os.path.exists(temp_wav):
                        pcm_bytes = _convertir_wav_a_pcm_16k_mono(temp_wav)
                        if pcm_bytes:
                            esp32_comm.reproducir_audio_bocina_pcm(pcm_bytes)
                else:
                    # Si no hay circuito conectado, reproducir por bocinas locales de PC como respaldo
                    engine.say(texto_limpio)
                    engine.runAndWait()

            except Exception as e:
                print(f"[TTS ERR] {e}")
            finally:
                if os.path.exists(temp_wav):
                    try:
                        os.remove(temp_wav)
                    except Exception:
                        pass
                try:
                    if esp32_comm.conectado:
                        esp32_comm.enviar_comando_oled("IDLE")
                except Exception:
                    pass

    threading.Thread(target=_run_tts, daemon=True).start()
