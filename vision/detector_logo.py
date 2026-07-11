"""
Detector de logotipos de criptomonedas usando ORB (Oriented FAST and Rotated BRIEF).
Compara features del frame de la cámara contra descriptores precalculados de logos conocidos.
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
    """Detector de logotipos basado en ORB feature matching."""
    
    def __init__(self):
        self.orb = cv2.ORB_create(nfeatures=ORB_N_FEATURES)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        self.descriptores_db = {}  # {nombre_cripto: [lista de descriptores]}
        self.modelo_cargado = False
    
    def cargar_modelo(self, ruta=None):
        """
        Carga los descriptores ORB precalculados desde un archivo pickle.
        
        Args:
            ruta: Ruta al archivo .pkl con los descriptores.
        
        Returns:
            True si se cargó correctamente, False si no.
        """
        ruta = ruta or ORB_DESCRIPTORS_FILE
        
        if not os.path.exists(ruta):
            print(f"[DetectorORB] No se encontró el modelo en: {ruta}")
            return False
        
        try:
            with open(ruta, 'rb') as f:
                self.descriptores_db = pickle.load(f)
            
            self.modelo_cargado = True
            n_clases = len(self.descriptores_db)
            n_total = sum(len(descs) for descs in self.descriptores_db.values())
            print(f"[DetectorORB] Modelo cargado: {n_clases} clases, {n_total} imágenes de referencia")
            return True
        except Exception as e:
            print(f"[DetectorORB] Error al cargar modelo: {e}")
            return False
    
    def detectar(self, frame):
        """
        Detecta un logotipo de criptomoneda en el frame dado.
        
        Args:
            frame: Imagen BGR (numpy array) de la cámara.
        
        Returns:
            tuple (nombre_cripto, confianza) o (None, 0.0) si no se detectó nada.
            confianza es un valor entre 0 y 1.
        """
        if not self.modelo_cargado or not self.descriptores_db:
            return None, 0.0
        
        # Convertir a escala de grises
        gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detectar keypoints y descriptores en el frame
        kp_frame, desc_frame = self.orb.detectAndCompute(gris, None)
        
        if desc_frame is None or len(kp_frame) < 5:
            return None, 0.0
        
        mejor_cripto = None
        mejor_confianza = 0.0
        
        for nombre, lista_descriptores in self.descriptores_db.items():
            # Comparar contra cada imagen de referencia de esta cripto
            max_confianza_clase = 0.0
            
            for desc_ref in lista_descriptores:
                if desc_ref is None:
                    continue
                
                try:
                    # Usar knnMatch para aplicar ratio test de Lowe
                    matches = self.bf.knnMatch(desc_ref, desc_frame, k=2)
                    
                    # Aplicar ratio test
                    buenos = []
                    for m_pair in matches:
                        if len(m_pair) == 2:
                            m, n = m_pair
                            if m.distance < 0.75 * n.distance:
                                buenos.append(m)
                    
                    n_buenos = len(buenos)
                    
                    if n_buenos >= ORB_MIN_MATCHES:
                        # Calcular confianza como ratio de buenos matches
                        confianza = n_buenos / max(len(desc_ref), 1)
                        confianza = min(confianza, 1.0)  # Clampar a 1.0
                        max_confianza_clase = max(max_confianza_clase, confianza)
                except Exception:
                    continue
            
            if max_confianza_clase > mejor_confianza:
                mejor_confianza = max_confianza_clase
                mejor_cripto = nombre
        
        if mejor_confianza >= ORB_CONFIDENCE_THRESHOLD:
            return mejor_cripto, mejor_confianza
        
        return None, 0.0
    
    def obtener_clases(self):
        """Retorna la lista de criptomonedas que el detector conoce."""
        return list(self.descriptores_db.keys())
    
    def esta_listo(self):
        """Verifica si el detector tiene un modelo cargado."""
        return self.modelo_cargado and len(self.descriptores_db) > 0
