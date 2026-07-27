import os
import sys
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json

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
    Transcribe un búfer de audio PCM de 16-bit / 16kHz proveniente del hardware INMP441.
    """
    if not os.path.exists(MODEL_DIR):
        return "Error: No se encontró el modelo de voz en 'modelo_vosk'."

    try:
        model = Model(MODEL_DIR)
        samplerate = 16000
        rec = KaldiRecognizer(model, samplerate)

        rec.AcceptWaveform(bytes(pcm_bytes))
        res = json.loads(rec.FinalResult())
        texto = res.get("text", "")
        return texto if texto else "No se reconoció el comando de voz."
    except Exception as e:
        return f"Error en STT: {e}"
