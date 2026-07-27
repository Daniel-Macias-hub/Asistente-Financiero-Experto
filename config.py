"""
Configuración global del Asistente Financiero Multimodal.
Centraliza todas las constantes, rutas y parámetros del sistema.
"""
import os

# === Rutas del Proyecto ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "conocimiento.db")
DATASET_PATH = os.path.join(BASE_DIR, "dataset_crypto")
MODELOS_VISION_PATH = os.path.join(BASE_DIR, "modelos_vision")
ORB_DESCRIPTORS_FILE = os.path.join(MODELOS_VISION_PATH, "orb_descriptors.pkl")
MODEL_VOSK_DIR = os.path.join(BASE_DIR, "modelo_vosk")

# === APIs Financieras ===
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
BINANCE_BASE_URL = "https://api.binance.com/api/v3"
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "")

# === Caché ===
CACHE_TTL_SECONDS = 60  # Tiempo de vida del caché de precios en segundos

# === Cámara ===
CAMERA_INDEX = 0  # Índice de la cámara (0 = cámara principal)
CAMERA_RESOLUTION = (640, 480)
CAMERA_FPS_UPDATE_MS = 33  # ~30 FPS para actualización del canvas

# === Visión (ORB) ===
ORB_N_FEATURES = 1200  # Cantidad de features a detectar
ORB_MIN_MATCHES = 8    # Mínimo de matches para considerar detección válida (sensible a ESP32-CAM)
ORB_CONFIDENCE_THRESHOLD = 0.08  # Umbral mínimo de confianza
DETECTION_CONSECUTIVE_FRAMES = 1  # Frames consecutivos para confirmar detección

# === Mapeo de Criptomonedas ===
# nombre_local → coingecko_id, binance_symbol
CRYPTO_MAP = {
    "bitcoin":   {"coingecko_id": "bitcoin",         "symbol": "BTC", "binance": "BTCUSDT"},
    "ethereum":  {"coingecko_id": "ethereum",         "symbol": "ETH", "binance": "ETHUSDT"},
    "solana":    {"coingecko_id": "solana",           "symbol": "SOL", "binance": "SOLUSDT"},
    "cardano":   {"coingecko_id": "cardano",          "symbol": "ADA", "binance": "ADAUSDT"},
    "xrp":       {"coingecko_id": "ripple",           "symbol": "XRP", "binance": "XRPUSDT"},
    "dogecoin":  {"coingecko_id": "dogecoin",         "symbol": "DOGE", "binance": "DOGEUSDT"},
    "bnb":       {"coingecko_id": "binancecoin",      "symbol": "BNB", "binance": "BNBUSDT"},
    "avalanche": {"coingecko_id": "avalanche-2",      "symbol": "AVAX", "binance": "AVAXUSDT"},
    "chainlink": {"coingecko_id": "chainlink",        "symbol": "LINK", "binance": "LINKUSDT"},
    "polkadot":  {"coingecko_id": "polkadot",         "symbol": "DOT", "binance": "DOTUSDT"},
    "litecoin":  {"coingecko_id": "litecoin",         "symbol": "LTC", "binance": "LTCUSDT"},
    "tron":      {"coingecko_id": "tron",             "symbol": "TRX", "binance": "TRXUSDT"},
}

# === Modo del Sistema ===
MODO_OFFLINE_FORZADO = False  # Si True, nunca intenta conectarse a Internet
