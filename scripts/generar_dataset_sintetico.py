"""
Generador de Dataset de Logotipos de Criptomonedas y Reentrenamiento ORB
Crea imágenes de referencia sintéticas para bitcoin, dogecoin, ethereum, solana, cardano, xrp y bnb,
y genera los descriptores en modelos_vision/orb_descriptors.pkl.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import cv2
import numpy as np
from config import DATASET_PATH
from vision.entrenamiento_visual import reentrenar_descriptores

def crear_imagen_logo(nombre, color_bg, color_fg, texto_simbolo):
    img = np.full((300, 300, 3), color_bg, dtype=np.uint8)
    
    # Dibujar círculo contenedor
    cv2.circle(img, (150, 150), 120, color_fg, 10)
    
    # Dibujar formas geométricas internas según cripto
    if nombre == "bitcoin":
        # Símbolo B de Bitcoin
        cv2.putText(img, "B", (100, 200), cv2.FONT_HERSHEY_SIMPLEX, 4.5, color_fg, 12)
        cv2.line(img, (100, 60), (100, 240), color_fg, 8)
        cv2.line(img, (190, 60), (190, 240), color_fg, 8)
    elif nombre == "dogecoin":
        # Símbolo D de Dogecoin (D con barra horizontal)
        cv2.putText(img, "D", (90, 210), cv2.FONT_HERSHEY_SIMPLEX, 4.8, color_fg, 14)
        cv2.line(img, (60, 135), (145, 135), color_fg, 10)
    elif nombre == "ethereum":
        # Diamante de Ethereum
        pts1 = np.array([[150, 40], [230, 150], [150, 200], [70, 150]], np.int32)
        pts2 = np.array([[150, 210], [230, 160], [150, 260], [70, 160]], np.int32)
        cv2.polylines(img, [pts1], True, color_fg, 6)
        cv2.polylines(img, [pts2], True, color_fg, 6)
    elif nombre == "solana":
        # Barras paralelas
        cv2.rectangle(img, (70, 70), (230, 100), color_fg, -1)
        cv2.rectangle(img, (70, 135), (230, 165), color_fg, -1)
        cv2.rectangle(img, (70, 200), (230, 230), color_fg, -1)
    elif nombre == "cardano":
        # Círculos concéntricos
        cv2.circle(img, (150, 150), 60, color_fg, 6)
        cv2.circle(img, (150, 150), 30, color_fg, -1)
    elif nombre == "xrp":
        # Forma X
        cv2.line(img, (80, 80), (220, 220), color_fg, 12)
        cv2.line(img, (220, 80), (80, 220), color_fg, 12)
    elif nombre == "bnb":
        # Símbolo BNB
        cv2.putText(img, "BNB", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 3.2, color_fg, 10)

    return img

def generar_dataset():
    os.makedirs(DATASET_PATH, exist_ok=True)
    
    criptos = {
        "bitcoin":   ((240, 240, 240), (0, 153, 255), "BTC"),   # Naranja BTC
        "dogecoin":  ((240, 240, 240), (0, 180, 220), "DOGE"),  # Dorado Doge
        "ethereum":  ((240, 240, 240), (120, 80, 50), "ETH"),   # Azul/Gris ETH
        "solana":    ((30, 30, 30),    (255, 0, 128), "SOL"),   # Magenta SOL
        "cardano":   ((240, 240, 240), (200, 50, 0),  "ADA"),   # Azul ADA
        "xrp":       ((240, 240, 240), (50, 50, 50),  "XRP"),   # Negro XRP
        "bnb":       ((240, 240, 240), (0, 200, 240), "BNB")    # Amarillo BNB
    }

    for nombre, (bg, fg, sim) in criptos.items():
        clase_dir = os.path.join(DATASET_PATH, nombre)
        os.makedirs(clase_dir, exist_ok=True)
        
        # Generar rotaciones y variaciones
        base_img = crear_imagen_logo(nombre, bg, fg, sim)
        cv2.imwrite(os.path.join(clase_dir, "logo_base.png"), base_img)
        
        # Variación 1: Rotación 15 deg
        M1 = cv2.getRotationMatrix2D((150, 150), 15, 1.0)
        img_rot1 = cv2.warpAffine(base_img, M1, (300, 300))
        cv2.imwrite(os.path.join(clase_dir, "logo_rot15.png"), img_rot1)

        # Variación 2: Escala
        img_scaled = cv2.resize(base_img, (240, 240))
        canvas = np.full((300, 300, 3), bg, dtype=np.uint8)
        canvas[30:270, 30:270] = img_scaled
        cv2.imwrite(os.path.join(clase_dir, "logo_scaled.png"), canvas)

    print("[Dataset] Logos base creados exitosamente.")
    exito, msg = reentrenar_descriptores()
    print(f"[Dataset] {msg}")

if __name__ == "__main__":
    generar_dataset()
