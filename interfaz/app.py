import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading

# Importar módulos de nuestro sistema experto
from experto.motor import procesar_consulta
from experto.finanzas_tiempo_real import obtener_datos_accion
from entrenamiento.agregar_concepto import nuevo_concepto
from entrenamiento.agregar_relacion import nueva_relacion
from entrenamiento.agregar_regla import nueva_regla
from audio.tts import hablar
from audio.stt import escuchar
from conocimiento.database import get_connection

# --- Configuración de Tema Oscuro Premium ---
BG_COLOR = "#121212"
CARD_COLOR = "#1E1E1E"
ENTRY_BG_COLOR = "#2A2A2A"
TEXT_COLOR = "#FFFFFF"
MUTED_TEXT = "#B3B3B3"
ACCENT_COLOR = "#00D287"  # Verde financiero
ACCENT_HOVER = "#00A96B"
FONT_MAIN = ("Segoe UI", 11)
FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_CODE = ("Consolas", 11)

class AsistenteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Asistente Experto en Bolsa y Finanzas")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        # Iniciar la ventana maximizada por defecto
        try:
            self.root.state("zoomed")
        except tk.TclError:
            pass
        self.root.configure(bg=BG_COLOR)
        
        self.configurar_estilos()
        self.crear_widgets()
        
    def configurar_estilos(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Notebook (Pestañas)
        self.style.configure("TNotebook", background=BG_COLOR, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=CARD_COLOR, foreground=TEXT_COLOR, 
                             padding=[20, 10], font=("Segoe UI", 11, "bold"), borderwidth=1, relief="solid", focuscolor=ACCENT_COLOR)
        self.style.map("TNotebook.Tab", 
                       background=[("selected", ACCENT_COLOR)], 
                       foreground=[("selected", "#000000")])
        
        # Frames
        self.style.configure("TFrame", background=BG_COLOR)
        self.style.configure("Card.TFrame", background=CARD_COLOR, relief="flat")
        
        # Labels
        self.style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR, font=FONT_MAIN)
        self.style.configure("Card.TLabel", background=CARD_COLOR, foreground=TEXT_COLOR, font=FONT_MAIN)
        self.style.configure("Title.TLabel", background=CARD_COLOR, foreground=ACCENT_COLOR, font=FONT_TITLE)
        
        # Buttons
        self.style.configure("TButton", font=("Segoe UI", 11, "bold"), background=ACCENT_COLOR, foreground="#000000",
                             borderwidth=1, relief="solid", padding=12, bordercolor=ACCENT_COLOR)
        self.style.map("TButton", background=[("active", ACCENT_HOVER)])
        
        # Entries
        self.style.configure("TEntry", fieldbackground=ENTRY_BG_COLOR, foreground=TEXT_COLOR, 
                             borderwidth=0, padding=10, font=FONT_MAIN)

    def crear_widgets(self):
        # Header
        header = ttk.Frame(self.root, style="Card.TFrame")
        header.pack(fill='x', pady=(0, 10))
        ttk.Label(header, text="🧠 ASISTENTE EDUCATIVO FINANCIERO", style="Title.TLabel", padding=15).pack(anchor="center")

        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=20, pady=10)
        
        self.tab_consulta = ttk.Frame(self.notebook, style="TFrame")
        self.tab_mercado = ttk.Frame(self.notebook, style="TFrame")
        self.tab_entrenamiento = ttk.Frame(self.notebook, style="TFrame")
        self.tab_conocimiento = ttk.Frame(self.notebook, style="TFrame")
        
        self.notebook.add(self.tab_consulta, text="💬 Consultas y Asesoría")
        self.notebook.add(self.tab_mercado, text="📈 Mercado en Tiempo Real")
        self.notebook.add(self.tab_entrenamiento, text="⚙️ Entrenamiento Base de Conocimiento")
        self.notebook.add(self.tab_conocimiento, text="📚 Base de Conocimiento")
        
        self.configurar_tab_consulta()
        self.configurar_tab_mercado()
        self.configurar_tab_entrenamiento()
        self.configurar_tab_conocimiento()
        
        # Recargar la base de conocimiento cada vez que se selecciona la pestaña
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

    def configurar_tab_consulta(self):
        # Contenedor principal de consulta
        container = ttk.Frame(self.tab_consulta, style="Card.TFrame")
        container.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Área de entrada (SE EMPAQUETA PRIMERO ABAJO PARA NO PERDERSE AL ENCOGER)
        frame_input = ttk.Frame(container, style="Card.TFrame")
        frame_input.pack(side=tk.BOTTOM, fill='x', padx=20, pady=20)
        
        btn_voz = ttk.Button(frame_input, text="🎙️ Hablar", command=self.consultar_voz)
        btn_voz.pack(side=tk.RIGHT, padx=5)
        
        btn_enviar = ttk.Button(frame_input, text="➤ Enviar", command=self.consultar_texto)
        btn_enviar.pack(side=tk.RIGHT, padx=5)

        self.entry_consulta = tk.Entry(
            frame_input, font=FONT_MAIN, bg=ENTRY_BG_COLOR, fg=TEXT_COLOR, 
            insertbackground=TEXT_COLOR, relief="flat",
            highlightthickness=1, highlightbackground=CARD_COLOR, highlightcolor=ACCENT_COLOR
        )
        self.entry_consulta.pack(side=tk.LEFT, expand=True, fill='x', ipady=12, padx=(0, 15))
        self.entry_consulta.bind("<Return>", lambda e: self.consultar_texto())
        
        # Historial de conversación (SE EMPAQUETA DESPUÉS PARA OCUPAR EL RESTO)
        self.historial = scrolledtext.ScrolledText(
            container, state='disabled', wrap=tk.WORD, 
            font=FONT_MAIN, bg=ENTRY_BG_COLOR, fg=TEXT_COLOR, 
            insertbackground=TEXT_COLOR, borderwidth=0, padx=20, pady=20,
            highlightthickness=1, highlightbackground=CARD_COLOR, highlightcolor=ACCENT_COLOR
        )
        self.historial.pack(side=tk.TOP, expand=True, fill='both')
        
        # Tag configuration para chat
        self.historial.tag_config('user', foreground=ACCENT_COLOR, font=("Segoe UI", 12, "bold"))
        self.historial.tag_config('bot', foreground=TEXT_COLOR)
        self.historial.tag_config('log', foreground=MUTED_TEXT, font=FONT_CODE)
        
        self.agregar_mensaje("Asistente", "¡Hola! Soy tu asistente financiero local. Puedes preguntarme sobre bolsa, riesgo, ETFs, etc.\n", "bot")

    def _on_tab_change(self, event):
        selected = self.notebook.index(self.notebook.select())
        # La pestaña de Base de Conocimiento es la índice 3
        if selected == 3:
            self.recargar_conocimiento()

    def configurar_tab_conocimiento(self):
        container = ttk.Frame(self.tab_conocimiento, style="Card.TFrame")
        container.pack(expand=True, fill='both', padx=10, pady=10)

        # Barra superior con título y botón de refrescar
        frame_top = ttk.Frame(container, style="Card.TFrame")
        frame_top.pack(fill='x', padx=20, pady=(15, 5))
        ttk.Label(frame_top, text="Conceptos en la Base de Conocimiento",
                  style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Button(frame_top, text="🔄 Actualizar",
                   command=self.recargar_conocimiento).pack(side=tk.RIGHT)

        # Contador de registros
        self.lbl_conteo = ttk.Label(container,
            text="", style="Card.TLabel",
            font=("Segoe UI", 10))
        self.lbl_conteo.pack(anchor='e', padx=25)

        # ── Sub-notebook: Conceptos / Relaciones / Reglas ──
        sub_nb = ttk.Notebook(container)
        sub_nb.pack(expand=True, fill='both', padx=15, pady=10)

        # -- Pestaña Conceptos --
        frame_conceptos = ttk.Frame(sub_nb, style="TFrame")
        sub_nb.add(frame_conceptos, text="💡 Conceptos")

        cols_c = ("#", "Nombre", "Definición")
        self.tree_conceptos = ttk.Treeview(frame_conceptos, columns=cols_c,
                                           show='headings', selectmode='browse')
        self._configurar_treeview(self.tree_conceptos,
                                   [("#", 40), ("Nombre", 160), ("Definición", 600)])
        self.tree_conceptos.pack(expand=True, fill='both', padx=5, pady=5)

        # -- Pestaña Relaciones --
        frame_relaciones = ttk.Frame(sub_nb, style="TFrame")
        sub_nb.add(frame_relaciones, text="🔗 Relaciones Semánticas")

        cols_r = ("#", "Origen", "Tipo de Relación", "Destino")
        self.tree_relaciones = ttk.Treeview(frame_relaciones, columns=cols_r,
                                            show='headings', selectmode='browse')
        self._configurar_treeview(self.tree_relaciones,
                                   [("#", 40), ("Origen", 160),
                                    ("Tipo de Relación", 200), ("Destino", 160)])
        self.tree_relaciones.pack(expand=True, fill='both', padx=5, pady=5)

        # -- Pestaña Reglas --
        frame_reglas = ttk.Frame(sub_nb, style="TFrame")
        sub_nb.add(frame_reglas, text="⚡ Reglas de Inferencia")

        cols_reg = ("#", "Condición", "Conclusión")
        self.tree_reglas = ttk.Treeview(frame_reglas, columns=cols_reg,
                                        show='headings', selectmode='browse')
        self._configurar_treeview(self.tree_reglas,
                                   [("#", 40), ("Condición", 250), ("Conclusión", 500)])
        self.tree_reglas.pack(expand=True, fill='both', padx=5, pady=5)

        # Cargar datos al inicio
        self.recargar_conocimiento()

    def _configurar_treeview(self, tree, columnas):
        """Aplica estilos y anchos a un Treeview."""
        style_name = f"{id(tree)}.Treeview"
        s = ttk.Style()
        s.configure(style_name,
                     background=ENTRY_BG_COLOR,
                     foreground=TEXT_COLOR,
                     fieldbackground=ENTRY_BG_COLOR,
                     rowheight=30,
                     font=FONT_MAIN)
        s.configure(f"{style_name}.Heading",
                     background=CARD_COLOR,
                     foreground=ACCENT_COLOR,
                     font=("Segoe UI", 11, "bold"),
                     relief="flat")
        s.map(style_name, background=[("selected", ACCENT_COLOR)],
                           foreground=[("selected", "#000000")])
        tree.configure(style=style_name)

        for col, width in columnas:
            tree.heading(col, text=col)
            tree.column(col, width=width, minwidth=30,
                        anchor='w' if col != "#" else 'center')

        # Scrollbar vertical
        sb = ttk.Scrollbar(tree.master, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    def recargar_conocimiento(self):
        """Lee la BD y actualiza los tres Treeviews."""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # -- Conceptos --
            cursor.execute("SELECT id, nombre, definicion FROM conceptos ORDER BY nombre")
            conceptos = cursor.fetchall()
            self.tree_conceptos.delete(*self.tree_conceptos.get_children())
            for i, row in enumerate(conceptos, 1):
                tag = 'even' if i % 2 == 0 else 'odd'
                self.tree_conceptos.insert('', 'end',
                    values=(i, row['nombre'].capitalize(), row['definicion']),
                    tags=(tag,))
            self.tree_conceptos.tag_configure('odd',  background=ENTRY_BG_COLOR)
            self.tree_conceptos.tag_configure('even', background=CARD_COLOR)

            # -- Relaciones --
            cursor.execute("SELECT id, origen, tipo_relacion, destino FROM relaciones ORDER BY origen")
            relaciones = cursor.fetchall()
            self.tree_relaciones.delete(*self.tree_relaciones.get_children())
            for i, row in enumerate(relaciones, 1):
                tag = 'even' if i % 2 == 0 else 'odd'
                self.tree_relaciones.insert('', 'end',
                    values=(i, row['origen'].capitalize(),
                            row['tipo_relacion'], row['destino'].capitalize()),
                    tags=(tag,))
            self.tree_relaciones.tag_configure('odd',  background=ENTRY_BG_COLOR)
            self.tree_relaciones.tag_configure('even', background=CARD_COLOR)

            # -- Reglas --
            cursor.execute("SELECT id, condicion, conclusion FROM reglas ORDER BY condicion")
            reglas = cursor.fetchall()
            self.tree_reglas.delete(*self.tree_reglas.get_children())
            for i, row in enumerate(reglas, 1):
                tag = 'even' if i % 2 == 0 else 'odd'
                self.tree_reglas.insert('', 'end',
                    values=(i, row['condicion'], row['conclusion']),
                    tags=(tag,))
            self.tree_reglas.tag_configure('odd',  background=ENTRY_BG_COLOR)
            self.tree_reglas.tag_configure('even', background=CARD_COLOR)

            conn.close()

            total = len(conceptos)
            self.lbl_conteo.config(
                text=f"📊  {total} concepto(s)  |  {len(relaciones)} relación(es)  |  {len(reglas)} regla(s)")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la base de conocimiento:\n{e}")

    def configurar_tab_entrenamiento(self):
        # Sub-pestañas
        sub_notebook = ttk.Notebook(self.tab_entrenamiento)
        sub_notebook.pack(expand=True, fill='both', padx=10, pady=10)
        
        frame_concepto = ttk.Frame(sub_notebook, style="Card.TFrame")
        frame_relacion = ttk.Frame(sub_notebook, style="Card.TFrame")
        frame_regla = ttk.Frame(sub_notebook, style="Card.TFrame")
        
        sub_notebook.add(frame_concepto, text="Añadir Concepto")
        sub_notebook.add(frame_relacion, text="Añadir Relación Semántica")
        sub_notebook.add(frame_regla, text="Añadir Regla de Inferencia")
        
        self.configurar_ui_concepto(frame_concepto)
        self.configurar_ui_relacion(frame_relacion)
        self.configurar_ui_regla(frame_regla)

    def configurar_tab_mercado(self):
        container = ttk.Frame(self.tab_mercado, style="Card.TFrame")
        container.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Búsqueda
        frame_top = ttk.Frame(container, style="Card.TFrame")
        frame_top.pack(fill='x', padx=20, pady=20)
        
        ttk.Label(frame_top, text="Buscar Ticker (ej. AAPL, MSFT):", style="Card.TLabel").pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(frame_top, text="🔍 Consultar", command=self.buscar_ticker).pack(side=tk.RIGHT)
        
        self.entry_ticker = tk.Entry(
            frame_top, font=FONT_MAIN, bg=ENTRY_BG_COLOR, fg=TEXT_COLOR, 
            relief="flat", insertbackground=TEXT_COLOR,
            highlightthickness=1, highlightbackground=CARD_COLOR, highlightcolor=ACCENT_COLOR
        )
        self.entry_ticker.pack(side=tk.LEFT, expand=True, fill='x', ipady=8, padx=(0, 15))
        self.entry_ticker.bind("<Return>", lambda e: self.buscar_ticker())

        # Resultados
        self.resultado_mercado = scrolledtext.ScrolledText(
            container, state='disabled', wrap=tk.WORD, 
            font=FONT_MAIN, bg=ENTRY_BG_COLOR, fg=TEXT_COLOR, 
            insertbackground=TEXT_COLOR, borderwidth=0, padx=20, pady=20,
            highlightthickness=1, highlightbackground=CARD_COLOR, highlightcolor=ACCENT_COLOR
        )
        self.resultado_mercado.pack(expand=True, fill='both', padx=20, pady=(0, 20))

    def buscar_ticker(self):
        ticker = self.entry_ticker.get().strip()
        if not ticker: return
        
        self.resultado_mercado.config(state='normal')
        self.resultado_mercado.delete("1.0", tk.END)
        self.resultado_mercado.insert(tk.END, f"Consultando datos para {ticker.upper()}...\n\n")
        self.resultado_mercado.config(state='disabled')
        self.root.update()
        
        def tarea():
            datos = obtener_datos_accion(ticker)
            self.root.after(0, self.mostrar_datos_ticker, datos, ticker)
            
        threading.Thread(target=tarea, daemon=True).start()

    def mostrar_datos_ticker(self, datos, ticker):
        self.resultado_mercado.config(state='normal')
        self.resultado_mercado.delete("1.0", tk.END)
        if not datos:
            self.resultado_mercado.insert(tk.END, f"❌ No se pudo obtener información para el ticker '{ticker.upper()}'.\nVerifica que esté escrito correctamente o intenta más tarde.")
        else:
            tendencia = "📈" if datos['cambio_porcentaje'] and datos['cambio_porcentaje'] >= 0 else "📉"
            cambio_str = f"{datos['cambio_porcentaje']:.2f}%" if datos['cambio_porcentaje'] else "N/A"
            
            texto = (
                f"🏢 Empresa: {datos['nombre']} ({datos['ticker']})\n"
                f"💰 Precio Actual: {datos['precio']} {datos['moneda']} {tendencia} ({cambio_str})\n"
                f"📊 Cierre Anterior: {datos['cierre_anterior']} {datos['moneda']}\n\n"
                f"📖 Resumen:\n{datos['resumen']}\n"
            )
            self.resultado_mercado.insert(tk.END, texto)
            
        self.resultado_mercado.config(state='disabled')

    def configurar_ui_concepto(self, frame):
        # Usamos grid para responsividad
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="Nuevo Concepto Financiero", style="Title.TLabel").grid(row=0, column=0, pady=(20, 10))
        ttk.Label(frame, text="Nombre del Concepto:", style="Card.TLabel").grid(row=1, column=0, pady=(10, 5), sticky="w", padx=40)
        self.entry_nombre_concepto = tk.Entry(
            frame, font=FONT_MAIN, bg=ENTRY_BG_COLOR, fg=TEXT_COLOR, relief="flat",
            highlightthickness=1, highlightbackground=CARD_COLOR, highlightcolor=ACCENT_COLOR
        )
        self.entry_nombre_concepto.grid(row=2, column=0, sticky="ew", padx=40, ipady=8)
        
        ttk.Label(frame, text="Definición exacta:", style="Card.TLabel").grid(row=3, column=0, pady=(20, 5), sticky="w", padx=40)
        self.text_definicion = tk.Text(
            frame, height=5, font=FONT_MAIN, bg=ENTRY_BG_COLOR, fg=TEXT_COLOR, relief="flat",
            highlightthickness=1, highlightbackground=CARD_COLOR, highlightcolor=ACCENT_COLOR
        )
        self.text_definicion.grid(row=4, column=0, sticky="nsew", padx=40, pady=5)
        frame.rowconfigure(4, weight=1)
        
        ttk.Button(frame, text="💾 Guardar Concepto", command=self.guardar_concepto).grid(row=5, column=0, pady=30)

    def configurar_ui_relacion(self, frame):
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="Red Semántica", style="Title.TLabel").grid(row=0, column=0, pady=(20, 10))
        
        ttk.Label(frame, text="Concepto Origen:", style="Card.TLabel").grid(row=1, column=0, pady=(10, 5), sticky="w", padx=40)
        self.entry_origen = tk.Entry(
            frame, font=FONT_MAIN, bg=ENTRY_BG_COLOR, fg=TEXT_COLOR, relief="flat",
            highlightthickness=1, highlightbackground=CARD_COLOR, highlightcolor=ACCENT_COLOR
        )
        self.entry_origen.grid(row=2, column=0, sticky="ew", padx=40, ipady=8)
        
        ttk.Label(frame, text="Tipo de Relación (Ej. 'es un', 'reduce'):", style="Card.TLabel").grid(row=3, column=0, pady=(10, 5), sticky="w", padx=40)
        self.entry_tipo_relacion = tk.Entry(
            frame, font=FONT_MAIN, bg=ENTRY_BG_COLOR, fg=TEXT_COLOR, relief="flat",
            highlightthickness=1, highlightbackground=CARD_COLOR, highlightcolor=ACCENT_COLOR
        )
        self.entry_tipo_relacion.grid(row=4, column=0, sticky="ew", padx=40, ipady=8)
        
        ttk.Label(frame, text="Concepto Destino:", style="Card.TLabel").grid(row=5, column=0, pady=(10, 5), sticky="w", padx=40)
        self.entry_destino = tk.Entry(
            frame, font=FONT_MAIN, bg=ENTRY_BG_COLOR, fg=TEXT_COLOR, relief="flat",
            highlightthickness=1, highlightbackground=CARD_COLOR, highlightcolor=ACCENT_COLOR
        )
        self.entry_destino.grid(row=6, column=0, sticky="ew", padx=40, ipady=8)
        
        ttk.Button(frame, text="🔗 Conectar Conceptos", command=self.guardar_relacion).grid(row=7, column=0, pady=30)

    def configurar_ui_regla(self, frame):
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="Motor de Inferencia (Reglas)", style="Title.TLabel").grid(row=0, column=0, pady=(20, 10))
        
        ttk.Label(frame, text="Condición (Keywords de usuario):", style="Card.TLabel").grid(row=1, column=0, pady=(10, 5), sticky="w", padx=40)
        self.entry_condicion = tk.Entry(
            frame, font=FONT_MAIN, bg=ENTRY_BG_COLOR, fg=TEXT_COLOR, relief="flat",
            highlightthickness=1, highlightbackground=CARD_COLOR, highlightcolor=ACCENT_COLOR
        )
        self.entry_condicion.grid(row=2, column=0, sticky="ew", padx=40, ipady=8)
        
        ttk.Label(frame, text="Conclusión a aplicar:", style="Card.TLabel").grid(row=3, column=0, pady=(10, 5), sticky="w", padx=40)
        self.entry_conclusion = tk.Entry(
            frame, font=FONT_MAIN, bg=ENTRY_BG_COLOR, fg=TEXT_COLOR, relief="flat",
            highlightthickness=1, highlightbackground=CARD_COLOR, highlightcolor=ACCENT_COLOR
        )
        self.entry_conclusion.grid(row=4, column=0, sticky="ew", padx=40, ipady=8)
        
        ttk.Button(frame, text="⚡ Añadir Regla", command=self.guardar_regla).grid(row=5, column=0, pady=30)

    # --- Acciones de Consulta ---
    def agregar_mensaje(self, autor, texto, tag):
        self.historial.config(state='normal')
        if autor == "Usuario":
            self.historial.insert(tk.END, f"\nTú: ", 'user')
            self.historial.insert(tk.END, f"{texto}\n", 'bot')
        elif autor == "Log":
            self.historial.insert(tk.END, f"  [+] {texto}\n", 'log')
        else:
            self.historial.insert(tk.END, f"\n🤖 Asistente: ", 'user')
            self.historial.insert(tk.END, f"{texto}\n", 'bot')
            
        self.historial.see(tk.END)
        self.historial.config(state='disabled')
        
    def procesar_respuesta(self, texto_usuario):
        self.agregar_mensaje("Usuario", texto_usuario, "user")
        
        respuesta, log_inferencia = procesar_consulta(texto_usuario)
        
        for l in log_inferencia:
            self.agregar_mensaje("Log", l, "log")
            
        self.agregar_mensaje("Asistente", respuesta, "bot")
        
        # Reproducir voz
        threading.Thread(target=hablar, args=(respuesta,), daemon=True).start()
        
    def consultar_texto(self):
        texto = self.entry_consulta.get().strip()
        if not texto: return
        self.entry_consulta.delete(0, tk.END)
        self.procesar_respuesta(texto)
        
    def consultar_voz(self):
        self.agregar_mensaje("Log", "Escuchando... Por favor, habla al micrófono.", "log")
        self.root.update()
        
        def hilo_voz():
            texto_reconocido = escuchar()
            if "Error" in texto_reconocido:
                self.agregar_mensaje("Log", texto_reconocido, "log")
            else:
                self.root.after(0, self.procesar_respuesta, texto_reconocido)
                
        threading.Thread(target=hilo_voz, daemon=True).start()

    # --- Acciones de Entrenamiento ---
    def guardar_concepto(self):
        nombre = self.entry_nombre_concepto.get().strip()
        definicion = self.text_definicion.get("1.0", tk.END).strip()
        if nombre and definicion:
            exito, msj = nuevo_concepto(nombre, definicion)
            messagebox.showinfo("Resultado", msj)
            if exito:
                self.entry_nombre_concepto.delete(0, tk.END)
                self.text_definicion.delete("1.0", tk.END)
        else:
            messagebox.showwarning("Faltan datos", "Completa nombre y definición.")

    def guardar_relacion(self):
        o = self.entry_origen.get().strip()
        d = self.entry_destino.get().strip()
        t = self.entry_tipo_relacion.get().strip()
        if o and d and t:
            exito, msj = nueva_relacion(o, d, t)
            messagebox.showinfo("Resultado", msj)
            if exito:
                self.entry_origen.delete(0, tk.END)
                self.entry_destino.delete(0, tk.END)
                self.entry_tipo_relacion.delete(0, tk.END)
        else:
            messagebox.showwarning("Faltan datos", "Completa origen, destino y relación.")

    def guardar_regla(self):
        cond = self.entry_condicion.get().strip()
        concl = self.entry_conclusion.get().strip()
        if cond and concl:
            exito, msj = nueva_regla(cond, concl)
            messagebox.showinfo("Resultado", msj)
            if exito:
                self.entry_condicion.delete(0, tk.END)
                self.entry_conclusion.delete(0, tk.END)
        else:
            messagebox.showwarning("Faltan datos", "Completa condición y conclusión.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AsistenteApp(root)
    root.mainloop()
