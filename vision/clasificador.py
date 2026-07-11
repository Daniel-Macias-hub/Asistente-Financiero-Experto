"""
Clasificador unificado de logotipos.
Proporciona una interfaz de alto nivel que selecciona automáticamente
entre ORB y YOLO según disponibilidad, y aplica filtrado temporal.
"""
from config import DETECTION_CONSECUTIVE_FRAMES


class ClasificadorLogo:
    """
    Clasificador de logotipos con filtrado temporal.
    Requiere detección consistente en N frames consecutivos antes de confirmar.
    """
    
    def __init__(self):
        self.detector = None
        self.tipo_detector = None
        self.historial = []  # Últimas N detecciones
        self.n_confirmacion = DETECTION_CONSECUTIVE_FRAMES
        
    def inicializar(self):
        """
        Inicializa el mejor detector disponible.
        Prioridad: YOLOv8 > ORB
        
        Returns:
            True si se inicializó algún detector, False si no.
        """
        # Intentar ORB (siempre disponible si OpenCV está instalado)
        try:
            from vision.detector_logo import DetectorORB
            detector = DetectorORB()
            if detector.cargar_modelo():
                self.detector = detector
                self.tipo_detector = "ORB"
                print(f"[Clasificador] Usando detector ORB con {len(detector.obtener_clases())} clases")
                return True
            else:
                print("[Clasificador] Detector ORB inicializado pero sin modelo entrenado.")
                self.detector = detector  # Mantener para reentrenar después
                self.tipo_detector = "ORB (sin modelo)"
                return False
        except ImportError:
            print("[Clasificador] OpenCV no disponible. Módulo de visión deshabilitado.")
            return False
    
    def clasificar(self, frame):
        """
        Clasifica un frame y aplica filtrado temporal.
        
        Args:
            frame: Imagen BGR (numpy array).
        
        Returns:
            tuple (nombre_cripto, confianza) si hay detección confirmada,
            (None, 0.0) si no hay detección o no está confirmada aún.
        """
        if self.detector is None or not self.detector.esta_listo():
            return None, 0.0
        
        nombre, confianza = self.detector.detectar(frame)
        
        # Agregar al historial
        self.historial.append(nombre)
        
        # Mantener solo los últimos N
        if len(self.historial) > self.n_confirmacion:
            self.historial = self.historial[-self.n_confirmacion:]
        
        # Verificar consistencia
        if len(self.historial) >= self.n_confirmacion:
            # ¿Todos los últimos N frames detectaron la misma cripto?
            if all(h == nombre for h in self.historial) and nombre is not None:
                return nombre, confianza
        
        return None, 0.0
    
    def clasificar_instantaneo(self, frame):
        """
        Clasifica sin filtrado temporal (para snapshots individuales).
        
        Args:
            frame: Imagen BGR.
        
        Returns:
            tuple (nombre_cripto, confianza).
        """
        if self.detector is None or not self.detector.esta_listo():
            return None, 0.0
        
        return self.detector.detectar(frame)
    
    def resetear_historial(self):
        """Limpia el historial de detecciones."""
        self.historial = []
    
    def obtener_clases(self):
        """Retorna las clases que el detector conoce."""
        if self.detector:
            return self.detector.obtener_clases()
        return []
    
    def esta_listo(self):
        """Verifica si el clasificador tiene un detector funcional."""
        return self.detector is not None and self.detector.esta_listo()
    
    def obtener_info(self):
        """Retorna información sobre el estado del clasificador."""
        return {
            "tipo": self.tipo_detector or "No inicializado",
            "listo": self.esta_listo(),
            "clases": len(self.obtener_clases()),
            "nombres": self.obtener_clases(),
        }
