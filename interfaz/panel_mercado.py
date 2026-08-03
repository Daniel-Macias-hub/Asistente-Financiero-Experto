"""
Panel de Mercado en Tiempo Real.
Dashboard que muestra precios y datos de las principales criptomonedas.
Se actualiza automáticamente cada 60 segundos cuando hay conexión.
"""
import tkinter as tk
from tkinter import ttk
import threading
import time

from interfaz.estilos import (
    BG_COLOR, CARD_COLOR, TEXT_COLOR, MUTED_TEXT, ACCENT_COLOR,
    SUCCESS_COLOR, ERROR_COLOR, WARNING_COLOR,
    FONT_MAIN, FONT_TITLE, FONT_SUBTITLE, FONT_SMALL, FONT_PRICE, INPUT_BG
)


class PanelMercado:
    """Panel dashboard con información de mercado en tiempo real."""
    
    def __init__(self, parent_frame, root):
        """
        Args:
            parent_frame: Frame padre (pestaña del notebook).
            root: Ventana raíz de Tkinter.
        """
        self.root = root
        self.frame = parent_frame
        self.actualizando = False
        self.auto_update_id = None
        self.crear_widgets()
        # Iniciar primera actualización
        self.root.after(500, self.actualizar_datos)
        
    def crear_widgets(self):
        # Contenedor principal
        container = ttk.Frame(self.frame, style="Card.TFrame")
        container.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Header del panel
        header = ttk.Frame(container, style="Card.TFrame")
        header.pack(fill='x', padx=20, pady=(15, 5))
        
        ttk.Label(header, text="📊 Mercado de Criptomonedas", 
                  style="Title.TLabel").pack(side=tk.LEFT)
        
        # Status y botones
        btn_frame = ttk.Frame(header, style="Card.TFrame")
        btn_frame.pack(side=tk.RIGHT)
        
        self.lbl_status = ttk.Label(btn_frame, text="⏳ Cargando...", 
                                     style="Muted.TLabel")
        self.lbl_status.pack(side=tk.LEFT, padx=(0, 15))
        
        self.btn_actualizar = ttk.Button(btn_frame, text="🔄 Actualizar", 
                                          command=self.actualizar_datos)
        self.btn_actualizar.pack(side=tk.LEFT)
        
        # Separador
        sep = tk.Frame(container, bg=ACCENT_COLOR, height=2)
        sep.pack(fill='x', padx=20, pady=10)
        
        # Tabla de criptomonedas
        self.crear_tabla(container)
        
        # Área de búsqueda manual
        self.crear_busqueda(container)
        
    def crear_tabla(self, container):
        """Crea la tabla/treeview con los datos del mercado."""
        # Frame para la tabla
        tabla_frame = ttk.Frame(container, style="Card.TFrame")
        tabla_frame.pack(fill='both', expand=True, padx=20, pady=5)
        
        # Configurar Treeview
        columnas = ("ranking", "nombre", "simbolo", "precio", "cambio_24h", "market_cap", "volumen")
        self.tree = ttk.Treeview(tabla_frame, columns=columnas, show='headings', 
                                  height=12, style="Custom.Treeview")
        
        # Configurar estilo del Treeview
        style = ttk.Style()
        style.configure("Custom.Treeview", 
                        background=CARD_COLOR, 
                        foreground=TEXT_COLOR,
                        fieldbackground=CARD_COLOR,
                        font=FONT_MAIN,
                        rowheight=35)
        style.configure("Custom.Treeview.Heading",
                        background=BG_COLOR,
                        foreground=ACCENT_COLOR,
                        font=("Segoe UI", 11, "bold"))
        style.map("Custom.Treeview",
                  background=[("selected", ACCENT_COLOR)],
                  foreground=[("selected", "#000000")])
        
        # Definir encabezados
        encabezados = {
            "ranking": ("#", 50),
            "nombre": ("Nombre", 130),
            "simbolo": ("Símbolo", 80),
            "precio": ("Precio (USD)", 140),
            "cambio_24h": ("Cambio 24h", 110),
            "market_cap": ("Cap. Mercado", 150),
            "volumen": ("Volumen 24h", 150),
        }
        
        for col, (titulo, ancho) in encabezados.items():
            self.tree.heading(col, text=titulo)
            anchor = tk.CENTER if col in ("ranking", "simbolo", "cambio_24h") else tk.E if col in ("precio", "market_cap", "volumen") else tk.W
            self.tree.column(col, width=ancho, anchor=anchor, minwidth=60)
        
        # Tags para colores de cambio
        self.tree.tag_configure('positivo', foreground=SUCCESS_COLOR)
        self.tree.tag_configure('negativo', foreground=ERROR_COLOR)
        self.tree.tag_configure('neutro', foreground=TEXT_COLOR)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tabla_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar.pack(side=tk.RIGHT, fill='y')
        
    def crear_busqueda(self, container):
        """Crea el área de búsqueda manual de criptomonedas."""
        busqueda_frame = ttk.Frame(container, style="Card.TFrame")
        busqueda_frame.pack(fill='x', padx=20, pady=(10, 20))
        
        ttk.Label(busqueda_frame, text="Buscar cripto:", 
                  style="Card.TLabel").pack(side=tk.LEFT, padx=(0, 10))
        
        self.entry_busqueda = tk.Entry(
            busqueda_frame, font=FONT_MAIN, bg=INPUT_BG, fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR, relief="flat", width=25
        )
        self.entry_busqueda.pack(side=tk.LEFT, ipady=8, padx=(0, 10))
        self.entry_busqueda.bind("<Return>", lambda e: self.buscar_cripto())
        
        ttk.Button(busqueda_frame, text="🔍 Buscar", 
                   command=self.buscar_cripto).pack(side=tk.LEFT)
        
        self.lbl_resultado = ttk.Label(busqueda_frame, text="", 
                                        style="Card.TLabel")
        self.lbl_resultado.pack(side=tk.LEFT, padx=(20, 0))
        
    def actualizar_datos(self):
        """Actualiza los datos del mercado en un hilo separado."""
        if self.actualizando:
            return
        self.actualizando = True
        self.lbl_status.config(text="⏳ Actualizando...")
        self.btn_actualizar.config(state="disabled")
        
        def hilo_actualizar():
            try:
                from api_financiera.conexion import modo_actual
                modo = modo_actual()
                
                datos = []
                if modo == "online":
                    try:
                        from api_financiera.coingecko import obtener_top_criptos
                        datos = obtener_top_criptos(12)
                        if datos:
                            # Guardar en caché
                            from api_financiera.cache import guardar_en_cache
                            for c in datos:
                                guardar_en_cache(c["nombre"].lower(), c)
                    except Exception as e:
                        print(f"[Panel Mercado] Error API: {e}")
                
                if not datos:
                    # Fallback a caché
                    from api_financiera.cache import obtener_todo_cache
                    datos = obtener_todo_cache()
                    modo = "offline (caché)"
                
                # Actualizar UI en el hilo principal
                self.root.after(0, self._actualizar_tabla, datos, modo)
            except Exception as e:
                self.root.after(0, self._mostrar_error, str(e))
            finally:
                self.actualizando = False
                self.root.after(0, lambda: self.btn_actualizar.config(state="normal"))
                # Programar siguiente actualización automática (60s)
                if self.auto_update_id:
                    self.root.after_cancel(self.auto_update_id)
                self.auto_update_id = self.root.after(60000, self.actualizar_datos)
        
        threading.Thread(target=hilo_actualizar, daemon=True).start()
        
    def _actualizar_tabla(self, datos, modo):
        """Actualiza la tabla con nuevos datos (debe ejecutarse en hilo principal)."""
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not datos:
            self.lbl_status.config(text="⚠️ Sin datos disponibles")
            return
        
        for d in datos:
            ranking = d.get("ranking", "-")
            nombre = d.get("nombre", d.get("cripto_nombre", ""))
            simbolo = d.get("simbolo", "").upper()
            precio = d.get("precio_usd", 0)
            cambio = d.get("cambio_24h", 0)
            market_cap = d.get("market_cap", 0)
            volumen = d.get("volumen_24h", 0)
            
            # Formatear valores
            precio_str = f"${precio:,.2f}" if precio else "-"
            cambio_str = f"{'+' if cambio >= 0 else ''}{cambio:.2f}%"
            market_cap_str = self._formatear_numero(market_cap)
            volumen_str = self._formatear_numero(volumen)
            
            # Determinar tag de color
            tag = 'positivo' if cambio > 0 else 'negativo' if cambio < 0 else 'neutro'
            
            self.tree.insert('', tk.END, values=(
                ranking, nombre, simbolo, precio_str, cambio_str, 
                market_cap_str, volumen_str
            ), tags=(tag,))
        
        hora = time.strftime("%H:%M:%S")
        self.lbl_status.config(text=f"✅ Actualizado {hora} | Modo: {modo}")
        
    def _mostrar_error(self, error):
        """Muestra un error en el status."""
        self.lbl_status.config(text=f"❌ Error: {error}")
        
    def _formatear_numero(self, n):
        """Formatea números grandes con sufijos (B, M, K)."""
        if not n:
            return "-"
        if n >= 1_000_000_000_000:
            return f"${n/1_000_000_000_000:.2f}T"
        if n >= 1_000_000_000:
            return f"${n/1_000_000_000:.2f}B"
        if n >= 1_000_000:
            return f"${n/1_000_000:.2f}M"
        if n >= 1_000:
            return f"${n/1_000:.1f}K"
        return f"${n:,.2f}"
        
    def buscar_cripto(self):
        """Busca información de una criptomoneda específica."""
        nombre = self.entry_busqueda.get().strip().lower()
        if not nombre:
            return
        
        self.lbl_resultado.config(text="Buscando...")
        
        def hilo_buscar():
            try:
                from api_financiera.conexion import modo_actual
                from api_financiera.cache import obtener_de_cache, obtener_de_cache_sin_ttl
                
                datos = None
                if modo_actual() == "online":
                    try:
                        from api_financiera.coingecko import obtener_precio_simple
                        datos = obtener_precio_simple(nombre)
                        if datos:
                            from api_financiera.cache import guardar_en_cache
                            guardar_en_cache(nombre, datos)
                    except Exception:
                        pass
                
                if not datos:
                    datos = obtener_de_cache(nombre) or obtener_de_cache_sin_ttl(nombre)
                
                if datos:
                    precio = datos.get("precio_usd", 0)
                    cambio = datos.get("cambio_24h", 0)
                    signo = "+" if cambio >= 0 else ""
                    icono = "📈" if cambio >= 0 else "📉"
                    texto = f"{icono} {nombre.upper()}: ${precio:,.2f} USD | {signo}{cambio:.2f}%"
                else:
                    texto = f"No se encontró '{nombre}'"
                
                self.root.after(0, lambda: self.lbl_resultado.config(text=texto))
            except Exception as e:
                self.root.after(0, lambda: self.lbl_resultado.config(text=f"Error: {e}"))
        
        threading.Thread(target=hilo_buscar, daemon=True).start()
