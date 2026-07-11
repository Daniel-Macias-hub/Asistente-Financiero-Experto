"""
Panel de Cámara para detección de logotipos de criptomonedas.
Muestra el feed de la cámara en un Canvas de Tkinter con overlay de detección.
"""
import tkinter as tk
from tkinter import ttk
import threading
import cv2
from PIL import Image, ImageTk

from interfaz.estilos import (
    BG_COLOR, CARD_COLOR, TEXT_COLOR, MUTED_TEXT, ACCENT_COLOR,
    SUCCESS_COLOR, ERROR_COLOR, FONT_MAIN, FONT_TITLE, FONT_SUBTITLE, 
    FONT_SMALL, FONT_PRICE, INPUT_BG
)
from config import CAMERA_FPS_UPDATE_MS


class PanelCamara:
    """Panel con feed de cámara en vivo y detección de logotipos."""
    
    def __init__(self, parent_frame, root):
        self.root = root
        self.frame = parent_frame
        self.camara = None
        self.clasificador = None
        self.corriendo = False
        self.update_id = None
        self.ultima_deteccion = None
        self.crear_widgets()
        
    def crear_widgets(self):
        # Contenedor principal con 2 columnas
        container = ttk.Frame(self.frame, style="Card.TFrame")
        container.pack(expand=True, fill='both', padx=10, pady=10)
        
        # === Columna izquierda: Cámara ===
        col_izq = ttk.Frame(container, style="Card.TFrame")
        col_izq.pack(side=tk.LEFT, expand=True, fill='both', padx=(10, 5), pady=10)
        
        ttk.Label(col_izq, text="📷 Cámara en Vivo", style="Title.TLabel").pack(pady=(5, 10))
        
        # Canvas para el feed de video
        self.canvas = tk.Canvas(col_izq, width=640, height=480, bg="#000000", 
                                 highlightthickness=0)
        self.canvas.pack(pady=5)
        
        # Texto centrado en el canvas cuando la cámara está apagada
        self.canvas.create_text(320, 240, text="Cámara desactivada\nPresiona 'Iniciar' para comenzar",
                                fill=MUTED_TEXT, font=FONT_MAIN, justify="center", tags="placeholder")
        
        # Botones de control
        btn_frame = ttk.Frame(col_izq, style="Card.TFrame")
        btn_frame.pack(fill='x', pady=10, padx=20)
        
        self.btn_iniciar = ttk.Button(btn_frame, text="▶ Iniciar Cámara", 
                                       command=self.iniciar_camara)
        self.btn_iniciar.pack(side=tk.LEFT, padx=5, expand=True, fill='x')
        
        self.btn_detener = ttk.Button(btn_frame, text="⏹ Detener", 
                                       command=self.detener_camara)
        self.btn_detener.pack(side=tk.LEFT, padx=5, expand=True, fill='x')
        self.btn_detener.config(state="disabled")
        
        self.btn_capturar = ttk.Button(btn_frame, text="📸 Capturar", 
                                        command=self.capturar_snapshot)
        self.btn_capturar.pack(side=tk.LEFT, padx=5, expand=True, fill='x')
        
        # Status
        self.lbl_status_cam = ttk.Label(col_izq, text="Estado: Inactiva", 
                                         style="Muted.TLabel")
        self.lbl_status_cam.pack(pady=5)
        
        # === Columna derecha: Info del activo detectado ===
        col_der = ttk.Frame(container, style="Card.TFrame", width=300)
        col_der.pack(side=tk.RIGHT, fill='y', padx=(5, 10), pady=10)
        col_der.pack_propagate(False)
        
        ttk.Label(col_der, text="🔍 Activo Detectado", style="Title.TLabel").pack(pady=(10, 15))
        
        # Separador
        sep = tk.Frame(col_der, bg=ACCENT_COLOR, height=2)
        sep.pack(fill='x', padx=15, pady=5)
        
        # Info de la cripto detectada
        self.lbl_nombre_cripto = ttk.Label(col_der, text="---", style="Price.TLabel")
        self.lbl_nombre_cripto.pack(pady=(15, 5))
        
        self.lbl_confianza = ttk.Label(col_der, text="Confianza: ---", style="Muted.TLabel")
        self.lbl_confianza.pack(pady=2)
        
        sep2 = tk.Frame(col_der, bg="#333333", height=1)
        sep2.pack(fill='x', padx=15, pady=10)
        
        # Datos de mercado del activo
        self.lbl_precio = ttk.Label(col_der, text="Precio: ---", style="Card.TLabel")
        self.lbl_precio.pack(anchor='w', padx=20, pady=3)
        
        self.lbl_cambio = ttk.Label(col_der, text="Cambio 24h: ---", style="Card.TLabel")
        self.lbl_cambio.pack(anchor='w', padx=20, pady=3)
        
        self.lbl_marketcap = ttk.Label(col_der, text="Market Cap: ---", style="Card.TLabel")
        self.lbl_marketcap.pack(anchor='w', padx=20, pady=3)
        
        self.lbl_ranking = ttk.Label(col_der, text="Ranking: ---", style="Card.TLabel")
        self.lbl_ranking.pack(anchor='w', padx=20, pady=3)
        
        sep3 = tk.Frame(col_der, bg="#333333", height=1)
        sep3.pack(fill='x', padx=15, pady=10)
        
        self.lbl_descripcion = ttk.Label(col_der, text="", style="Muted.TLabel",
                                          wraplength=260, justify="left")
        self.lbl_descripcion.pack(anchor='w', padx=20, pady=5)
        
        # Detector info
        sep4 = tk.Frame(col_der, bg="#333333", height=1)
        sep4.pack(fill='x', padx=15, pady=10)
        
        self.lbl_detector_info = ttk.Label(col_der, text="Detector: No inicializado", 
                                            style="Muted.TLabel")
        self.lbl_detector_info.pack(anchor='w', padx=20, pady=3)

    def iniciar_camara(self):
        """Inicia la cámara y el loop de detección."""
        if self.corriendo:
            return
        
        # Inicializar cámara
        try:
            from vision.camara import CamaraManager
            self.camara = CamaraManager()
            if not self.camara.iniciar():
                self.lbl_status_cam.config(text="❌ Error: No se pudo abrir la cámara")
                return
        except ImportError:
            self.lbl_status_cam.config(text="❌ Error: OpenCV no instalado")
            return
        
        # Inicializar clasificador
        try:
            from vision.clasificador import ClasificadorLogo
            self.clasificador = ClasificadorLogo()
            self.clasificador.inicializar()
            info = self.clasificador.obtener_info()
            self.lbl_detector_info.config(
                text=f"Detector: {info['tipo']} | {info['clases']} clases"
            )
        except Exception as e:
            self.lbl_detector_info.config(text=f"Detector: Error ({e})")
            self.clasificador = None
        
        self.corriendo = True
        self.btn_iniciar.config(state="disabled")
        self.btn_detener.config(state="normal")
        self.lbl_status_cam.config(text="✅ Cámara activa")
        
        # Borrar placeholder del canvas
        self.canvas.delete("placeholder")
        
        # Iniciar loop de actualización
        self._actualizar_frame()
    
    def _actualizar_frame(self):
        """Loop de actualización del feed de cámara."""
        if not self.corriendo:
            return
        
        frame = self.camara.capturar_frame()
        if frame is not None:
            # Detectar logotipo si el clasificador está listo
            nombre_detectado = None
            confianza = 0.0
            
            if self.clasificador and self.clasificador.esta_listo():
                nombre_detectado, confianza = self.clasificador.clasificar(frame)
            
            # Dibujar overlay si hay detección
            if nombre_detectado:
                h, w = frame.shape[:2]
                # Borde verde
                cv2.rectangle(frame, (5, 5), (w-5, h-5), (0, 210, 135), 3)
                # Texto
                label = f"{nombre_detectado.upper()} ({confianza:.0%})"
                cv2.putText(frame, label, (15, 35), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 210, 135), 2)
                
                # Actualizar panel de info si es nueva detección
                if nombre_detectado != self.ultima_deteccion:
                    self.ultima_deteccion = nombre_detectado
                    self._mostrar_info_cripto(nombre_detectado, confianza)
            
            # Convertir frame para Tkinter
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((640, 480), Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(image=img)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        
        # Programar siguiente actualización
        self.update_id = self.root.after(CAMERA_FPS_UPDATE_MS, self._actualizar_frame)
    
    def _mostrar_info_cripto(self, nombre, confianza):
        """Muestra información del activo detectado en el panel lateral."""
        self.lbl_nombre_cripto.config(text=nombre.upper())
        self.lbl_confianza.config(text=f"Confianza: {confianza:.0%}")
        
        # Consultar datos en hilo separado
        def obtener_datos():
            try:
                from api_financiera.conexion import modo_actual
                from api_financiera.cache import obtener_de_cache, obtener_de_cache_sin_ttl, guardar_en_cache
                
                datos = None
                if modo_actual() == "online":
                    try:
                        from api_financiera.coingecko import obtener_info_cripto
                        datos = obtener_info_cripto(nombre)
                        if datos:
                            guardar_en_cache(nombre, datos)
                    except Exception:
                        pass
                
                if not datos:
                    datos = obtener_de_cache(nombre) or obtener_de_cache_sin_ttl(nombre)
                
                self.root.after(0, self._actualizar_panel_info, nombre, datos)
            except Exception as e:
                self.root.after(0, lambda: self.lbl_precio.config(text=f"Error: {e}"))
        
        threading.Thread(target=obtener_datos, daemon=True).start()
        
        # Narrar la detección por voz
        def narrar():
            try:
                from audio.tts import hablar
                hablar(f"He identificado {nombre}")
            except Exception:
                pass
        
        threading.Thread(target=narrar, daemon=True).start()
    
    def _actualizar_panel_info(self, nombre, datos):
        """Actualiza el panel lateral con datos del activo (en hilo principal)."""
        if datos:
            precio = datos.get("precio_usd", 0)
            cambio = datos.get("cambio_24h", 0)
            market_cap = datos.get("market_cap", 0)
            ranking = datos.get("ranking", "-")
            desc = datos.get("descripcion", "")
            
            signo = "+" if cambio >= 0 else ""
            color = SUCCESS_COLOR if cambio >= 0 else ERROR_COLOR
            
            self.lbl_precio.config(text=f"Precio: ${precio:,.2f} USD")
            self.lbl_cambio.config(text=f"Cambio 24h: {signo}{cambio:.2f}%", foreground=color)
            
            if market_cap:
                if market_cap >= 1_000_000_000:
                    mc_str = f"${market_cap/1_000_000_000:.2f}B"
                else:
                    mc_str = f"${market_cap:,.0f}"
                self.lbl_marketcap.config(text=f"Market Cap: {mc_str}")
            
            if ranking:
                self.lbl_ranking.config(text=f"Ranking: #{ranking}")
            
            if desc:
                # Truncar descripción si es muy larga
                desc_corta = desc[:200] + "..." if len(desc) > 200 else desc
                self.lbl_descripcion.config(text=desc_corta)
        else:
            self.lbl_precio.config(text="Precio: Sin datos")
            self.lbl_cambio.config(text="Cambio 24h: ---")
            self.lbl_marketcap.config(text="Market Cap: ---")
            self.lbl_ranking.config(text="Ranking: ---")
            self.lbl_descripcion.config(text="Conéctate a Internet para obtener datos.")
    
    def detener_camara(self):
        """Detiene la cámara y el loop de detección."""
        self.corriendo = False
        
        if self.update_id:
            self.root.after_cancel(self.update_id)
            self.update_id = None
        
        if self.camara:
            self.camara.detener()
            self.camara = None
        
        if self.clasificador:
            self.clasificador.resetear_historial()
        
        self.ultima_deteccion = None
        self.btn_iniciar.config(state="normal")
        self.btn_detener.config(state="disabled")
        self.lbl_status_cam.config(text="Estado: Inactiva")
        
        # Restaurar placeholder
        self.canvas.delete("all")
        self.canvas.create_text(320, 240, text="Cámara desactivada\nPresiona 'Iniciar' para comenzar",
                                fill=MUTED_TEXT, font=FONT_MAIN, justify="center", tags="placeholder")
    
    def capturar_snapshot(self):
        """Captura un frame individual para análisis."""
        if not self.corriendo:
            # Intentar snapshot rápido sin cámara continua
            try:
                from vision.camara import CamaraManager
                cam = CamaraManager()
                if cam.iniciar():
                    frame = cam.capturar_frame()
                    cam.detener()
                    if frame is not None and self.clasificador:
                        nombre, conf = self.clasificador.clasificar_instantaneo(frame)
                        if nombre:
                            self.lbl_status_cam.config(text=f"📸 Detectado: {nombre} ({conf:.0%})")
                            self._mostrar_info_cripto(nombre, conf)
                        else:
                            self.lbl_status_cam.config(text="📸 No se detectó ningún logotipo")
                else:
                    self.lbl_status_cam.config(text="❌ No se pudo abrir la cámara")
            except Exception as e:
                self.lbl_status_cam.config(text=f"❌ Error: {e}")
        else:
            self.lbl_status_cam.config(text="📸 Snapshot capturado (detección en curso)")
