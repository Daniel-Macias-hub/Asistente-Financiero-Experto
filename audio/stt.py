import os
import sys
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json
import numpy as np

# Ruta donde se espera el modelo de Vosk
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "modelo_vosk")

# Cola para almacenar el audio del micrófono local
q = queue.Queue()

def callback(indata, frames, time, status):
    """Callback para bloques de audio del micrófono de la PC."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def escuchar():
    """Escucha desde el micrófono de la PC."""
    if not os.path.exists(MODEL_DIR):
        return "Error: No se encontró el modelo de voz en 'modelo_vosk'."
        
    try:
        model = Model(MODEL_DIR)
        samplerate = 16000
        rec = KaldiRecognizer(model, samplerate)

        with sd.RawInputStream(samplerate=samplerate, blocksize=8000, dtype='int16', channels=1, callback=callback):
            print("Escuchando de micrófono PC... Habla ahora.")
            while True:
                data = q.get()
                if rec.AcceptWaveform(data):
                    resultado = rec.Result()
                    texto = json.loads(resultado).get("text", "")
                    if texto:
                        return texto
    except Exception as e:
        return f"Error en STT: {str(e)}"

def escuchar_desde_pcm(pcm_bytes: bytes) -> str:
    """
    Transcribe un búfer de audio PCM de 16-bit / 16kHz proveniente del hardware INMP441
    con eliminación de offset DC, normalización de ganancia automática y procesamiento en fragmentos.
    """
    if not os.path.exists(MODEL_DIR):
        return "Error: No se encontró el modelo de voz en 'modelo_vosk'."

    try:
        if not pcm_bytes or len(pcm_bytes) < 1000:
            return "No se recibió audio del micrófono INMP441."

        # Convertir a arreglo numpy para procesamiento digital de señal (DSP)
        audio_np = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32)

        # 1. Eliminar DC Offset
        audio_np -= np.mean(audio_np)

        # 2. Normalización de ganancia dinámica (amplificar voz baja a escala óptima)
        max_peak = np.max(np.abs(audio_np))
        if max_peak > 50:  # Evitar amplificar solo ruido blanco en silencio
            gain = 26000.0 / max_peak
            audio_np = np.clip(audio_np * gain, -32768, 32767)

        pcm_procesado = audio_np.astype(np.int16).tobytes()

        model = Model(MODEL_DIR)
        samplerate = 16000
        rec = KaldiRecognizer(model, samplerate)

        # 3. Alimentar a Vosk en fragmentos secuenciales de 2048 bytes para reconocimiento continuo de oraciones
        chunk_size = 2048
        for i in range(0, len(pcm_procesado), chunk_size):
            chunk = pcm_procesado[i:i+chunk_size]
            rec.AcceptWaveform(chunk)

        res = json.loads(rec.FinalResult())
        texto = res.get("text", "").strip()

        # Fallback a resultado parcial si FinalResult omitió alguna palabra
        if not texto:
            res_partial = json.loads(rec.PartialResult())
            texto = res_partial.get("partial", "").strip()

        return texto if texto else "No se reconoció el comando de voz."
    except Exception as e:
        return f"Error en STT: {e}"
