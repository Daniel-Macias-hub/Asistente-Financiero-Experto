"""
Detector de logotipos de criptomonedas — Sistema de dos capas:
  1. Gemini Vision API (online, ~99% precisión)
  2. ORB mejorado con filtro de color + consenso multi-frame (offline)
"""
import os
import cv2
import numpy as np
import base64
import json
import pickle
import requests as _requests
from dotenv import load_dotenv
from config import (
    ORB_N_FEATURES, MODELOS_VISION_PATH, ORB_DESCRIPTORS_FILE
)

load_dotenv()

# ── Colores dominantes por criptomoneda (HSV) para boost de confianza ─────────
COLOR_PROFILES = {
    "bitcoin":   (np.array([5,  120, 150]), np.array([25,  255, 255])),
    "ethereum":  (np.array([200, 20,  60]), np.array([260,  80, 180])),
    "cardano":   (np.array([100, 130, 100]),np.array([130, 255, 255])),
    "solana":    (np.array([140,  80,  80]),np.array([170, 255, 255])),
    "xrp":       (np.array([100,  40,  40]),np.array([140, 180, 220])),
    "dogecoin":  (np.array([20,  120, 150]),np.array([40,  255, 255])),
    "bnb":       (np.array([18,  150, 150]),np.array([35,  255, 255])),
}

# ── Gemini Vision Detector (Capa 1) ──────────────────────────────────────────
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-3.6-flash:generateContent"
)

PROMPT_CRIPTO = (
    "Analiza esta imagen minuciosamente e identifica si contiene el logotipo de una criptomoneda.\n\n"
    "CATÁLOGO DE CRIPTOMONEDAS SOPORTADAS:\n"
    "- Bitcoin (BTC): Círculo naranja o dorado con la letra 'B' y dos barras verticales.\n"
    "- Ethereum (ETH): Forma de octaedro / diamante geométrico plateado o azul.\n"
    "- Cardano (ADA): Círculo o esfera azul con patrón concéntrico de múltiples puntos blancos o símbolo ADA.\n"
    "- Solana (SOL): Tres barras paralelas diagonales o rectángulos con degradado morado, magenta y verde.\n"
    "- XRP / Ripple (XRP): Logotipo con letra 'X' o tres gotas conectadas en tono azul.\n"
    "- Dogecoin (DOGE): Cara del perro Shiba Inu amarillo o letra 'D' atravesada.\n"
    "- BNB / Binance (BNB): Diamante o cuadrados amarillos/dorados entrelazados o texto BNB.\n\n"
    "INSTRUCCIONES DE RESPUESTA:\n"
    "Responde ÚNICAMENTE con este JSON estrictamente estructurado, sin bloques de código markdown:\n"
    "{\"cripto\": \"nombre\", \"confianza\": 0.99, \"razon\": \"explicación breve de lo que observas\"}\n\n"
    "Reglas:\n"
    "1. 'nombre' debe ser EXCLUSIVAMENTE una de estas palabras clave en minúsculas: bitcoin, ethereum, cardano, solana, xrp, dogecoin, bnb.\n"
    "2. Si la imagen muestra claramente uno de los logotipos anteriores, la confianza debe ser entre 0.85 y 1.0.\n"
    "3. Si NO se detecta ningún logotipo conocido con claridad, responde: {\"cripto\": null, \"confianza\": 0.0, \"razon\": \"Sin coincidencias\"}"
)


class DetectorGeminiVision:
    """Usa Google Gemini 1.5 Flash para identificar logos con precision ~99%%."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.disponible = bool(api_key)

    def detectar(self, frame_bgr) -> tuple:
        """Returns: (nombre_cripto|None, confianza 0-1)"""
        if not self.disponible:
            return None, 0.0
        try:
            _, jpeg = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 88])
            img_b64 = base64.b64encode(jpeg.tobytes()).decode('utf-8')
            payload = {
                "contents": [{
                    "parts": [
                        {"text": PROMPT_CRIPTO},
                        {"inlineData": {"mimeType": "image/jpeg", "data": img_b64}}
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 512
                }
            }
            # Lista de modelos compatibles para failover automático si hay rate limit (429)
            modelos_gemini = [
                "gemini-3.6-flash",
                "gemini-2.0-flash",
                "gemini-flash-latest"
            ]

            for model_name in modelos_gemini:
                endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
                url = f"{endpoint}?key={self.api_key}"
                headers = {"Content-Type": "application/json"}
                try:
                    resp = _requests.post(url, json=payload, headers=headers, timeout=10)
                    if resp.status_code == 200:
                        texto = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                        cleaned = texto.replace("```json", "").replace("```", "").strip()
                        import re
                        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
                        if match:
                            r = json.loads(match.group(0))
                            cripto = r.get("cripto")
                            confianza = float(r.get("confianza", 0.0))
                            if cripto and str(cripto).lower() != "null" and confianza > 0.3:
                                return str(cripto).lower().strip(), confianza
                    elif resp.status_code == 429:
                        # Cuota por minuto alcanzada, esperar brevemente e intentar siguiente modelo
                        time.sleep(1.0)
                        continue
                except Exception:
                    continue
            return None, 0.0





        except Exception as e:
            print(f"[GeminiVision] Error: {e}")
            return None, 0.0


# ── ORB Detector mejorado (Capa 2 / Fallback offline) ────────────────────────

class DetectorORB:
    """ORB mejorado con boost de color HSV y consenso de ultimos 5 frames."""

    def __init__(self):
        self.orb = cv2.ORB_create(nfeatures=2000, scaleFactor=1.2, nlevels=8)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        self.descriptores_db = {}
        self.modelo_cargado = False
        self.clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        self._hist: list = []

    def cargar_modelo(self, ruta=None):
        ruta = ruta or ORB_DESCRIPTORS_FILE
        if not os.path.exists(ruta):
            print(f"[DetectorORB] Modelo no encontrado: {ruta}")
            return False
        try:
            with open(ruta, 'rb') as f:
                self.descriptores_db = pickle.load(f)
            self.modelo_cargado = True
            return True
        except Exception as e:
            print(f"[DetectorORB] Error al cargar modelo: {e}")
            return False

    def _color_boost(self, frame_bgr, nombre: str) -> float:
        if nombre not in COLOR_PROFILES:
            return 0.0
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        lo, hi = COLOR_PROFILES[nombre]
        mask = cv2.inRange(hsv, lo, hi)
        return min(1.0, np.count_nonzero(mask) / mask.size * 6.0)

    def detectar(self, frame_bgr) -> tuple:
        """Returns: (nombre|None, confianza 0-1)"""
        if not self.modelo_cargado or not self.descriptores_db:
            return None, 0.0
        gris = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        gris_eq = self.clahe.apply(gris)
        kp_frame, desc_frame = self.orb.detectAndCompute(gris_eq, None)
        if desc_frame is None or len(kp_frame) < 4:
            return None, 0.0

        scores = {}
        for nombre, lista_desc in self.descriptores_db.items():
            max_buenos = 0
            for desc_ref in lista_desc:
                if desc_ref is None or len(desc_ref) < 2:
                    continue
                try:
                    matches = self.bf.knnMatch(desc_ref, desc_frame, k=2)
                    buenos = sum(
                        1 for pair in matches
                        if len(pair) == 2 and pair[0].distance < 0.78 * pair[1].distance
                    )
                    if buenos > max_buenos:
                        max_buenos = buenos
                except Exception:
                    continue
            scores[nombre] = max_buenos + self._color_boost(frame_bgr, nombre) * 3

        if not scores:
            return None, 0.0
        mejor = max(scores, key=scores.get)
        melhor_score = scores[mejor]
        if melhor_score >= 8:
            confianza_orb = min(0.95, melhor_score / 15.0)
            self._hist.append(mejor)
            if len(self._hist) > 5:
                self._hist.pop(0)
            votos = self._hist.count(mejor)
            confianza_final = confianza_orb * (0.6 + 0.4 * (votos / 5))
            if confianza_final >= 0.60:
                return mejor, round(confianza_final, 2)

        return None, 0.0

    def obtener_clases(self):
        return list(self.descriptores_db.keys())

    def esta_listo(self):
        return self.modelo_cargado and bool(self.descriptores_db)


# ── Detector Unificado: Gemini (online) → ORB (offline) ──────────────────────

class DetectorCriptoUnificado:
    """
    Usa Gemini Vision si hay API key (GEMINI_API_KEY en .env).
    Cae automaticamente a ORB mejorado si no hay internet o key.
    Returns: (nombre|None, confianza, modo:'gemini'|'orb'|'none')
    """

    def __init__(self):
        load_dotenv()
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        self.gemini = DetectorGeminiVision(api_key)
        self.orb = DetectorORB()
        self.orb.cargar_modelo()

    def detectar(self, frame_bgr) -> tuple:
        if self.gemini.disponible:
            cripto, conf = self.gemini.detectar(frame_bgr)
            if cripto and conf >= 0.70:
                return cripto, conf, "gemini"
        if self.orb.esta_listo():
            cripto, conf = self.orb.detectar(frame_bgr)
            if cripto and conf >= 0.75:
                return cripto, conf, "orb"
        return None, 0.0, "none"


