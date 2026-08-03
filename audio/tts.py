import re
import threading
import os
import wave
import numpy as np
import asyncio

_tts_lock = threading.Lock()

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

def resumir_texto_para_hablar(texto_limpio: str, max_chars: int = 280) -> str:
    """Extrae un resumen hablado fluido y sintético para evitar audios excesivamente largos."""
    if not texto_limpio or len(texto_limpio) <= max_chars:
        return texto_limpio
    corte = texto_limpio[:max_chars]
    pos_punto = corte.rfind('.')
    if pos_punto > 80:
        return corte[:pos_punto + 1]
    pos_esp = corte.rfind(' ')
    if pos_esp > 80:
        return corte[:pos_esp] + "."
    return corte + "."

def _aplicar_filtro_audio_limpio(pcm_samples: np.ndarray, sample_rate: int = 8000) -> np.ndarray:
    """Aplica un filtro pasa-bajas suave (3.5kHz) para eliminar asperezas digitales y darle calidez y nitidez a la bocina."""
    try:
        from scipy.signal import butter, filtfilt
        cutoff = 3500.0
        nyq = 0.5 * sample_rate
        normal_cutoff = min(0.95, cutoff / nyq)
        b, a = butter(2, normal_cutoff, btype='low', analog=False)
        filtered = filtfilt(b, a, pcm_samples.astype(np.float32))
        return np.clip(filtered, -32768, 32767).astype(np.int16)
    except Exception:
        return pcm_samples

def _generar_pcm_edge_tts(texto: str, sample_rate: int = 16000, amp_scale: float = 0.80) -> bytes:
    """Genera audio PCM 16kHz Mono 16-bit alineado para I2S Hardware."""
    try:
        import edge_tts
        import miniaudio

        async def _async_edge():
            voice = "es-MX-DaliaNeural"
            communicate = edge_tts.Communicate(texto, voice)
            mp3_bytes = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    mp3_bytes.extend(chunk["data"])
            return bytes(mp3_bytes)

        mp3_data = asyncio.run(_async_edge())
        if mp3_data and len(mp3_data) > 100:
            decoded = miniaudio.decode(mp3_data, nchannels=1, sample_rate=sample_rate)
            pcm_mono = np.frombuffer(decoded.samples, dtype=np.int16)
            pcm_mono = _aplicar_filtro_audio_limpio(pcm_mono, sample_rate=sample_rate)
            pcm_mono = (pcm_mono * amp_scale).astype(np.int16)
            # NO reordenar bytes: el firmware ESP32-S3 espera PCM16 Little Endian
            # (mismo formato que usa struct.pack_into("<h", ...) en el micrófono).
            # Invertir el orden de bytes aquí corrompe cada muestra y se percibe
            # como interferencia/estática en la bocina.
            return pcm_mono.tobytes()
    except Exception as ex_edge:
        import sys
        print(f"[EDGE-TTS ERR] {ex_edge}. Python: {sys.executable} (v{sys.version_info.major}.{sys.version_info.minor})")
    return b""

def _generar_pcm_gtts(texto: str, sample_rate: int = 16000, amp_scale: float = 0.80) -> bytes:
    """Fallback usando Google Text-to-Speech (gTTS) en Español Mono 16kHz."""
    try:
        from gtts import gTTS
        import miniaudio
        temp_mp3 = os.path.abspath(f"temp_gtts_{threading.get_ident()}.mp3")
        tts = gTTS(text=texto, lang='es', slow=False)
        tts.save(temp_mp3)
        if os.path.exists(temp_mp3):
            with open(temp_mp3, 'rb') as f:
                mp3_data = f.read()
            os.remove(temp_mp3)
            decoded = miniaudio.decode(mp3_data, nchannels=1, sample_rate=sample_rate)
            pcm_mono = np.frombuffer(decoded.samples, dtype=np.int16)
            pcm_mono = (pcm_mono * amp_scale).astype(np.int16)
            # Sin byteswap: mismo motivo que en _generar_pcm_edge_tts (Little Endian nativo)
            return pcm_mono.tobytes()
    except Exception as ex_gtts:
        print(f"[GTTS ERR] {ex_gtts}")
    return b""

def _convertir_wav_a_pcm_16k_mono(wav_path: str) -> bytes:
    """Lee un archivo WAV y lo remuestra a PCM 16kHz Mono 16-bit."""
    try:
        with wave.open(wav_path, 'rb') as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            raw_bytes = wf.readframes(n_frames)

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

        audio = (audio * 0.40).astype(np.int16)
        return audio.tobytes()
    except Exception as e:
        print(f"[WAV CONVERT ERR] {e}")
        return b""

_stop_event = threading.Event()
MODO_SALIDA_AUDIO = "ESP32"  # 'ESP32' (Principal), 'BOTH' (Ambos Lados), 'PC'

def set_modo_salida_audio(modo: str):
    global MODO_SALIDA_AUDIO
    if modo in ("ESP32", "BOTH", "PC"):
        MODO_SALIDA_AUDIO = modo
        print(f"[AUDIO] Modo de salida de audio configurado a: '{modo}'")

def detener_habla():
    """Detiene la reproducción de voz actual de forma inmediata en la PC y en la placa ESP32."""
    global _stop_event
    _stop_event.set()
    try:
        import sounddevice as sd
        sd.stop()
    except Exception:
        pass
    try:
        from comunicacion_esp32 import esp32_comm
        esp32_comm.cancelar_flag = True
        if esp32_comm.conectado:
            if esp32_comm.serial_conn:
                esp32_comm.serial_conn.write(b"STOP\n")
                # Eliminado flush() porque bloquea la GUI en Windows si el dispositivo deja de leer
            esp32_comm.enviar_comando_oled("IDLE")
            print("[AUDIO] 🛑 Voz detenida por el usuario.")
    except Exception as ex:
        print(f"[STOP ERR] {ex}")

def hablar(texto: str):
    """
    Sintetiza el texto usando Edge-TTS Neural HD / gTTS y lo transmite a la bocina del ESP32-S3 y/o Altavoces de la PC.
    """
    global _stop_event
    _stop_event.clear()

    texto_limpio = limpiar_texto_para_tts(texto)
    if not texto_limpio:
        return

    texto_sintesis = resumir_texto_para_hablar(texto_limpio, max_chars=280)

    def _run_tts():
        with _tts_lock:
            if _stop_event.is_set():
                return
            from comunicacion_esp32 import esp32_comm
            
            try:
                # 1. Intentar generar audio PCM con síntesis Neural HD (edge_tts) o gTTS
                pcm_bytes = _generar_pcm_edge_tts(texto_sintesis, sample_rate=16000, amp_scale=0.90)
                if not pcm_bytes:
                    pcm_bytes = _generar_pcm_gtts(texto_sintesis, sample_rate=16000, amp_scale=0.90)

                if _stop_event.is_set():
                    return

                # ── Ruta A: PCM generado correctamente (edge_tts / gTTS disponibles) ──
                if pcm_bytes:
                    # Aumentar volumen x2.5 para la bocina física (MAX98357A no tiene ganancia ajustable por software)
                    pcm_np = (np.frombuffer(pcm_bytes, dtype=np.int16) * 2.5).clip(-32768, 32767).astype(np.int16)
                    
                    # Prepend 250ms de silencio para des-mutear el amplificador MAX98357A
                    preambulo_silencio = b'\x00' * 8000
                    pcm_bytes = preambulo_silencio + pcm_np.tobytes()

                    # Reproducción en PC si modo PC o BOTH
                    if MODO_SALIDA_AUDIO in ("PC", "BOTH"):
                        def _play_pc_async():
                            try:
                                import sounddevice as sd
                                # pcm_np ya está amplificado
                                sd.play(pcm_np, 16000)
                                sd.wait()
                            except Exception as ex_pc:
                                print(f"[PC AUDIO ERR] {ex_pc}")
                        threading.Thread(target=_play_pc_async, daemon=True).start()

                    # Salida Principal: Bocina Física ESP32-S3
                    if MODO_SALIDA_AUDIO in ("ESP32", "BOTH"):
                        if not esp32_comm.conectado:
                            try:
                                esp32_comm.conectar("AUTO")
                            except Exception:
                                pass  # Fallo al conectar: se usará fallback PC

                        if esp32_comm.conectado:
                            print(f"[TTS NEURAL -> PCB ESP32] Transmitiendo {len(pcm_bytes)} bytes PCM a la bocina MAX98357A en {esp32_comm.puerto}...")
                            esp32_comm.reproducir_audio_bocina_pcm(pcm_bytes)
                        else:
                            # Fallback PCM → altavoces PC cuando ESP32 no disponible
                            try:
                                import sounddevice as sd
                                audio_np = np.frombuffer(pcm_bytes, dtype=np.int16)
                                sd.play(audio_np, 16000)
                                sd.wait()
                            except Exception as ex_pc:
                                print(f"[PC AUDIO ERR] {ex_pc}")

                else:
                    # ── Ruta B: edge_tts y gTTS no instalados → pyttsx3 respetando el selector ──
                    # Reproducir en PC solo si:
                    #   - Modo es "PC" o "BOTH" (el usuario lo pidió explícitamente), O
                    #   - Modo es "ESP32" pero el ESP32 no está conectado (fallback para no quedarse en silencio)
                    pc_permitido = MODO_SALIDA_AUDIO in ("PC", "BOTH") or (
                        MODO_SALIDA_AUDIO == "ESP32" and not esp32_comm.conectado
                    )
                    if pc_permitido:
                        print(f"[TTS] pyttsx3 en PC (modo={MODO_SALIDA_AUDIO}, ESP32={'conectado' if esp32_comm.conectado else 'desconectado'})")
                        def _hablar_pyttsx3():
                            try:
                                import pyttsx3
                                engine = pyttsx3.init()
                                # Voz en español si está disponible
                                for v in engine.getProperty('voices'):
                                    if 'spanish' in v.name.lower() or 'es' in v.id.lower():
                                        engine.setProperty('voice', v.id)
                                        break
                                engine.setProperty('rate', 160)
                                engine.setProperty('volume', 0.95)
                                engine.say(texto_sintesis)
                                engine.runAndWait()
                            except Exception as ex_pyttsx:
                                print(f"[PYTTSX3 ERR] {ex_pyttsx}")
                        threading.Thread(target=_hablar_pyttsx3, daemon=True).start()
                    else:
                        print(f"[TTS] Modo '{MODO_SALIDA_AUDIO}' con ESP32 conectado → audio reservado para bocina física.")

            except Exception as e:
                print(f"[TTS ERR] {e}")
            finally:
                try:
                    if esp32_comm.conectado:
                        esp32_comm.enviar_comando_oled("IDLE")
                except Exception:
                    pass

    threading.Thread(target=_run_tts, daemon=True).start()
