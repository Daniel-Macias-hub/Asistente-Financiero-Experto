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
            )

        # Atenuar la amplitud al 45% para evitar la saturación/recorte del hardware MAX98357A
        audio = (audio * 0.45).astype(np.int16)

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
            temp_wav = os.path.abspath(f"temp_speech_{threading.get_ident()}.wav")
            
            try:
                # 1. Intentar renderizar WAV de forma ultra-rápida y directa usando win32com SAPI5
                wav_generado = False
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                    try:
                        import win32com.client
                        stream = win32com.client.Dispatch("SAPI.SpFileStream")
                        # 3 = SSFMCreateForWrite
                        stream.Open(temp_wav, 3, False)
                        voice = win32com.client.Dispatch("SAPI.SpVoice")
                        voice.AudioOutputStream = stream
                        # Seleccionar voz en español si está disponible
                        for v in voice.GetVoices():
                            desc = v.GetDescription().lower()
                            if "sabina" in desc or "spanish" in desc or "es-" in desc or "mexico" in desc:
                                voice.Voice = v
                                break
                        voice.Speak(texto_limpio)
                        stream.Close()
                        wav_generado = os.path.exists(temp_wav) and os.path.getsize(temp_wav) > 100
                    finally:
                        pythoncom.CoUninitialize()
                except Exception as ex_sapi:
                    print(f"[SAPI NATIVE ERR] {ex_sapi}")

                # 2. Fallback a pyttsx3 si SAPI directo falló
                if not wav_generado:
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 155)
                    engine.save_to_file(texto_limpio, temp_wav)
                    engine.runAndWait()
                    wav_generado = os.path.exists(temp_wav) and os.path.getsize(temp_wav) > 100

                # 3. Transmitir audio PCM a la bocina del ESP32-S3 (COM11) o reproducir en PC
                if wav_generado:
                    pcm_bytes = _convertir_wav_a_pcm_16k_mono(temp_wav)
                    if pcm_bytes:
                        if not esp32_comm.conectado:
                            esp32_comm.conectar(esp32_comm.puerto or "COM5")

                        if esp32_comm.conectado:
                            print(f"[TTS -> PCB] Transmitiendo {len(pcm_bytes)} bytes PCM a la bocina MAX98357A en {esp32_comm.puerto}...")
                            esp32_comm.reproducir_audio_bocina_pcm(pcm_bytes)
                        else:
                            import sounddevice as sd
                            audio_np = np.frombuffer(pcm_bytes, dtype=np.int16)
                            sd.play(audio_np, 16000)
                            sd.wait()

            except Exception as e:
                print(f"[TTS ERR] {e}")
                if esp32_comm.conectado:
                    esp32_comm.ejecutar_test_audio()
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
