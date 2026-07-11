"""
Gestor de cámara web usando OpenCV.
Encapsula la captura de video para simplificar el uso en la interfaz.
"""
import cv2
from config import CAMERA_INDEX, CAMERA_RESOLUTION


class CamaraManager:
    """Gestiona la captura de video desde la cámara web."""
    
    def __init__(self, indice=None, resolucion=None):
        """
        Args:
            indice: Índice de la cámara (0 = principal).
            resolucion: Tupla (ancho, alto).
        """
        self.indice = indice if indice is not None else CAMERA_INDEX
        self.resolucion = resolucion or CAMERA_RESOLUTION
        self.cap = None
        
    def iniciar(self):
        """
        Abre la cámara web.
        
        Returns:
            True si se abrió correctamente, False si no.
        """
        try:
            self.cap = cv2.VideoCapture(self.indice, cv2.CAP_DSHOW)  # DirectShow en Windows
            if not self.cap.isOpened():
                # Fallback sin backend específico
                self.cap = cv2.VideoCapture(self.indice)
            
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolucion[0])
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolucion[1])
                return True
            return False
        except Exception as e:
            print(f"[Cámara] Error al iniciar: {e}")
            return False
    
    def capturar_frame(self):
        """
        Captura un frame de la cámara.
        
        Returns:
            Frame como numpy array (BGR), o None si hay error.
        """
        if self.cap is None or not self.cap.isOpened():
            return None
        
        ret, frame = self.cap.read()
        if ret:
            return frame
        return None
    
    def capturar_snapshot(self):
        """
        Captura un único snapshot (para cuando la cámara no está en modo continuo).
        Abre la cámara, captura un frame y la cierra.
        
        Returns:
            Frame como numpy array (BGR), o None.
        """
        if not self.esta_activa():
            if not self.iniciar():
                return None
        
        frame = self.capturar_frame()
        return frame
    
    def esta_activa(self):
        """
        Verifica si la cámara está abierta y funcionando.
        
        Returns:
            True si está activa, False si no.
        """
        return self.cap is not None and self.cap.isOpened()
    
    def detener(self):
        """Cierra la cámara y libera recursos."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
    
    def __del__(self):
        """Asegura liberación de recursos al destruir el objeto."""
        self.detener()
