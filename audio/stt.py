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

# Singleton del modelo Vosk — se carga una vez y se reutiliza en todas las llamadas
_vosk_model = None

def _get_vosk_model():
    """Devuelve el modelo Vosk, cargándolo la primera vez (singleton)."""
    global _vosk_model
    if _vosk_model is None:
        if not os.path.exists(MODEL_DIR):
            return None
        _vosk_model = Model(MODEL_DIR)
    return _vosk_model

def callback(indata, frames, time, status):
    """Callback para bloques de audio del micrófono de la PC."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def filtrar_ruido_y_normalizar(pcm_raw: bytes, sample_rate=16000) -> bytes:
    """
    Filtro DSP optimizado para micrófono:
    1. Eliminación de Offset DC.
    2. Filtro paso-alto suave (~120Hz) para eliminar zumbidos.
    3. Control Automático de Ganancia (AGC) sin recortar voz.
    """
    if not pcm_raw or len(pcm_raw) < 1600:
        return pcm_raw

    samples = np.frombuffer(pcm_raw, dtype=np.int16).astype(np.float32)

    # 1. Eliminación de Offset DC
    samples -= np.mean(samples)

    # 2. Filtro paso-alto suave (~120Hz)
    alpha = 0.95
    y = np.zeros_like(samples)
    y[0] = samples[0]
    for i in range(1, len(samples)):
        y[i] = samples[i] - samples[i-1] + alpha * y[i-1]
    samples = y

    # 3. AGC: Normalización de ganancia dinámica limpia
    max_peak = np.max(np.abs(samples))
    if max_peak > 30:
        gain = min(26000.0 / max_peak, 8.0)
        samples = np.clip(samples * gain, -32768, 32767)

    return samples.astype(np.int16).tobytes()

VOCABULARIO_FINANCIERO = [
    "qué es la inflación", "qué es la inflacion", "inflación", "inflacion",
    "cómo ahorrar dinero", "como ahorrar dinero", "ahorrar dinero", "ahorro",
    "qué es bitcoin", "que es bitcoin", "bitcoin", "btc", "precio de btc", "precio de bitcoin",
    "qué es un etf", "que es un etf", "etf", "fondo etf",
    "qué es el interés compuesto", "que es el interes compuesto", "interés compuesto", "interes compuesto",
    "cómo reducir riesgo", "como reducir riesgo", "reducir riesgo", "riesgo",
    "qué es un mercado alcista", "que es un mercado alcista", "mercado alcista", "alcista",
    "qué es el mercado de valores", "que es el mercado de valores", "mercado de valores", "bolsa de valores",
    "qué son las acciones", "que son las acciones", "acciones", "acción",
    "qué es un bono", "que es un bono", "bono", "bonos", "renta fija", "renta variable",
    "dividendo", "recesión", "recesion", "pib", "producto interno bruto",
    "precio de eth", "precio de ethereum", "ethereum", "eth",
    "precio de sol", "precio de solana", "solana", "sol",
    "pepe", "precio de pepe", "cripto pepe",
    "qué es un activo", "activo financiero", "pasivo", "diversificación", "presupuesto", "inversión",
    "instalación", "instalacion", "ciudad", "vete", "este ef", "es es", "como mismo tiempo",
    "[unk]"
]

_DYNAMIC_VOCAB = None

def _get_vocabulario_dinamico():
    global _DYNAMIC_VOCAB
    if _DYNAMIC_VOCAB is not None:
        return _DYNAMIC_VOCAB

    base = list(VOCABULARIO_FINANCIERO)
    base.extend(["qué", "que", "es", "la", "el", "los", "las", "un", "una", "precio", "de", "cómo", "como", "cuánto", "cuanto", "vale", "cotización", "cotizacion"])

    try:
        from conocimiento.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT nombre FROM conceptos")
        for row in cursor.fetchall():
            base.append(row['nombre'].lower())
            
        cursor.execute("SELECT sinonimo FROM sinonimos")
        for row in cursor.fetchall():
            base.append(row['sinonimo'].lower())
            
        cursor.execute("SELECT condicion FROM reglas")
        for row in cursor.fetchall():
            base.append(row['condicion'].lower())
            
        conn.close()
    except Exception as e:
        print(f"[STT] Error cargando vocabulario dinámico: {e}")
        
    _DYNAMIC_VOCAB = list(set([v.strip() for v in base if v.strip()]))
    return _DYNAMIC_VOCAB


def normalizar_fonetica_financiera(texto: str) -> str:
    """Corrige desviaciones fonéticas comunes del modelo de voz para términos financieros."""
    if not texto:
        return ""
    t = texto.lower().strip()

    reemplazos = {
        "instalación": "inflación",
        "instalacion": "inflación",
        "la instalación": "la inflación",
        "vete": "btc",
        "pete": "btc",
        "ve te ce": "btc",
        "be te ce": "btc",
        "e te e fe": "etf",
        "ete ef": "etf",
        "este ef": "etf",
        "como mismo tiempo": "interés compuesto",
        "es la la ciudad": "inflación",
        "interes": "interés compuesto",
    }
    for k, v in reemplazos.items():
        if k in t:
            t = t.replace(k, v)

    if t == "precio btc" or t == "btc" or t == "bitcoin":
        return "Precio de BTC"
    if "interés compuesto" in t or "interes compuesto" in t:
        return "¿Qué es el interés compuesto?"
    if "inflación" in t or "inflacion" in t:
        return "¿Qué es la inflación?"
    if "etf" in t:
        return "¿Qué es un ETF?"

    return t

def escuchar(duracion_sec=4.0):
    """Escucha desde el micrófono durante duracion_sec segundos con filtrado DSP y Vosk STT."""
    if not os.path.exists(MODEL_DIR):
        return "Error: No se encontró el modelo de voz en 'modelo_vosk'."
        
    try:
        # Vaciar cola previa
        while not q.empty():
            try:
                q.get_nowait()
            except Exception:
                break

        import time as _t
        t_start = _t.time()
        pcm_chunks = []

        samplerate = 16000
        with sd.RawInputStream(samplerate=samplerate, blocksize=2000, dtype='int16', channels=1, callback=callback):
            while _t.time() - t_start < duracion_sec:
                try:
                    data = q.get(timeout=0.1)
                    if data:
                        pcm_chunks.append(data)
                except Exception:
                    pass

        raw_pcm = b"".join(pcm_chunks)
        if not raw_pcm or len(raw_pcm) < 1600:
            return "No se reconoció el comando de voz."

        # Procesar con filtro DSP anti-ruido
        pcm_limpio = filtrar_ruido_y_normalizar(raw_pcm, samplerate)

        # Transcribir con Vosk STT (modelo precargado, sin delay de recarga)
        model = _get_vosk_model()
        if model is None:
            return "Error: No se encontró el modelo de voz en 'modelo_vosk'."
        try:
            vocab = _get_vocabulario_dinamico()
            rec = KaldiRecognizer(model, samplerate, json.dumps(vocab))
        except Exception:
            rec = KaldiRecognizer(model, samplerate)

        chunk_size = 2048
        for i in range(0, len(pcm_limpio), chunk_size):
            chunk = pcm_limpio[i:i+chunk_size]
            rec.AcceptWaveform(chunk)

        res_final = json.loads(rec.FinalResult())
        texto = res_final.get("text", "").strip()

        # Fallback a resultado parcial si FinalResult omitió texto
        if not texto:
            res_part = json.loads(rec.PartialResult())
            texto = res_part.get("partial", "").strip()

        return texto if texto else "No se reconoció el comando de voz."

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

        model = _get_vosk_model()
        if model is None:
            return "Error: No se encontró el modelo de voz en 'modelo_vosk'."
        samplerate = 16000
        try:
            vocab = _get_vocabulario_dinamico()
            rec = KaldiRecognizer(model, samplerate, json.dumps(vocab))
        except Exception:
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
