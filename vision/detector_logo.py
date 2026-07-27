"""
Detector de logotipos de criptomonedas usando ORB y ecualización adaptativa CLAHE.
Compara features del frame de la cámara contra descriptores de logos conocidos.
"""
import os
import pickle
import cv2
import numpy as np
from config import (
    ORB_N_FEATURES, ORB_MIN_MATCHES, ORB_CONFIDENCE_THRESHOLD,
    MODELOS_VISION_PATH, ORB_DESCRIPTORS_FILE
)

class DetectorORB:
    """Detector de logotipos basado en ORB feature matching con ecualización de contraste."""
    
    def __init__(self):
        self.orb = cv2.ORB_create(nfeatures=2000, scaleFactor=1.2, nlevels=8)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        self.descriptores_db = {}
        self.modelo_cargado = False
        self.clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8,8))
    
    def cargar_modelo(self, ruta=None):
        ruta = ruta or ORB_DESCRIPTORS_FILE
        if not os.path.exists(ruta):
            print(f"[DetectorORB] No se encontró el modelo en: {ruta}")
            return False
        
        try:
            with open(ruta, 'rb') as f:
                self.descriptores_db = pickle.load(f)
            self.modelo_cargado = True
            return True
        except Exception as e:
            print(f"[DetectorORB] Error al cargar modelo: {e}")
            return False
    
    def detectar(self, frame):
        """
        Detecta un logotipo de criptomoneda en el frame dado.
        """
        if not self.modelo_cargado or not self.descriptores_db:
            return None, 0.0
        
        # 1. Ecualización adaptativa de contraste CLAHE (elimina reflejos de pantallas de celular)
        gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gris_eq = self.clahe.apply(gris)
        
        # 2. Extraer descriptores ORB
        kp_frame, desc_frame = self.orb.detectAndCompute(gris_eq, None)
        
        if desc_frame is None or len(kp_frame) < 4:
            return None, 0.0
        
        mejor_cripto = None
        mejor_score = 0
        mejor_confianza = 0.0
        
        for nombre, lista_descriptores in self.descriptores_db.items():
            max_buenos_clase = 0
            
            for desc_ref in lista_descriptores:
                if desc_ref is None or len(desc_ref) < 2:
                    continue
                
                try:
                    matches = self.bf.knnMatch(desc_ref, desc_frame, k=2)
                    buenos = []
                    for m_pair in matches:
                        if len(m_pair) == 2:
                            m, n = m_pair
                            if m.distance < 0.78 * n.distance:
                                buenos.append(m)
                    
                    if len(buenos) > max_buenos_clase:
                        max_buenos_clase = len(buenos)
                except Exception:
                    continue
            
            if max_buenos_clase > mejor_score:
                mejor_score = max_buenos_clase
                mejor_cripto = nombre

        # Umbral adaptativo sensible a capturas de cámara
        if mejor_score >= 4:
            confianza = min(1.0, mejor_score / 15.0)
            return mejor_cripto, confianza
        
        return None, 0.0

    def obtener_clases(self):
        return list(self.descriptores_db.keys())

    def esta_listo(self):
        return self.modelo_cargado and len(self.descriptores_db) > 0
