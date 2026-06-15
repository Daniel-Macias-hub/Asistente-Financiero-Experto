import os
import sys
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json

# Ruta donde se espera el modelo de Vosk
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "modelo_vosk")

# Cola para almacenar el audio
q = queue.Queue()

def callback(indata, frames, time, status):
    """Esta función se llama para cada bloque de audio del micrófono."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def escuchar():
    """
    Abre el micrófono, escucha el audio del usuario y lo transcribe a texto usando Vosk.
    La función se bloquea hasta que el usuario deja de hablar.
    """
    if not os.path.exists(MODEL_DIR):
        return "Error: No se encontró el modelo de voz. Descárgalo y ponlo en la carpeta 'modelo_vosk'."
        
    try:
        model = Model(MODEL_DIR)
        samplerate = 16000
        rec = KaldiRecognizer(model, samplerate)

        # Configuramos sounddevice para capturar del micrófono por defecto
        with sd.RawInputStream(samplerate=samplerate, blocksize=8000, dtype='int16',
                               channels=1, callback=callback):
            print("Escuchando... Habla ahora.")
            while True:
                data = q.get()
                if rec.AcceptWaveform(data):
                    resultado = rec.Result()
                    texto = json.loads(resultado).get("text", "")
                    if texto:
                        return texto
                else:
                    # rec.PartialResult() se podría usar para mostrar texto en tiempo real
                    pass
    except Exception as e:
        return f"Error en STT: {str(e)}"
