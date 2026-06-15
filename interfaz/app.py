import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading

# Importar módulos de nuestro sistema experto
from experto.motor import procesar_consulta
from entrenamiento.agregar_concepto import nuevo_concepto
from entrenamiento.agregar_relacion import nueva_relacion
from entrenamiento.agregar_regla import nueva_regla
from audio.tts import hablar
from audio.stt import escuchar

# --- Configuración de Tema Oscuro Premium ---
BG_COLOR = "#121212"
CARD_COLOR = "#1E1E1E"
TEXT_COLOR = "#FFFFFF"
MUTED_TEXT = "#B3B3B3"
ACCENT_COLOR = "#00D287"  # Verde financiero
ACCENT_HOVER = "#00A96B"
FONT_MAIN = ("Segoe UI", 12)
FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_CODE = ("Consolas", 11)

class AsistenteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Asistente Experto en Bolsa y Finanzas")
        self.root.geometry("1000x700")
        self.root.configure(bg=BG_COLOR)
        
        self.configurar_estilos()
        self.crear_widgets()
        
    def configurar_estilos(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Notebook (Pestañas)
        self.style.configure("TNotebook", background=BG_COLOR, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=CARD_COLOR, foreground=TEXT_COLOR, 
                             padding=[20, 10], font=FONT_MAIN, borderwidth=0)
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
        self.style.configure("TButton", font=FONT_MAIN, background=ACCENT_COLOR, foreground="#000000",
                             borderwidth=0, padding=10)
        self.style.map("TButton", background=[("active", ACCENT_HOVER)])
        
        # Entries
        self.style.configure("TEntry", fieldbackground="#2A2A2A", foreground=TEXT_COLOR, 
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
        self.tab_entrenamiento = ttk.Frame(self.notebook, style="TFrame")
        
        self.notebook.add(self.tab_consulta, text="💬 Consultas y Asesoría")
        self.notebook.add(self.tab_entrenamiento, text="⚙️ Entrenamiento Base de Conocimiento")
        
        self.configurar_tab_consulta()
        self.configurar_tab_entrenamiento()

    def configurar_tab_consulta(self):
        # Contenedor principal de consulta
        container = ttk.Frame(self.tab_consulta, style="Card.TFrame")
        container.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Historial de conversación con diseño oscuro
        self.historial = scrolledtext.ScrolledText(
            container, state='disabled', wrap=tk.WORD, 
            font=FONT_MAIN, bg=CARD_COLOR, fg=TEXT_COLOR, 
            insertbackground=TEXT_COLOR, borderwidth=0, padx=20, pady=20
        )
        self.historial.pack(expand=True, fill='both')
        
        # Tag configuration para chat
        self.historial.tag_config('user', foreground=ACCENT_COLOR, font=("Segoe UI", 12, "bold"))
        self.historial.tag_config('bot', foreground=TEXT_COLOR)
        self.historial.tag_config('log', foreground=MUTED_TEXT, font=FONT_CODE)
        
        # Área de entrada
        frame_input = ttk.Frame(container, style="Card.TFrame")
        frame_input.pack(fill='x', padx=20, pady=20)
        
        self.entry_consulta = tk.Entry(
            frame_input, font=FONT_MAIN, bg="#2A2A2A", fg=TEXT_COLOR, 
            insertbackground=TEXT_COLOR, relief="flat"
        )
        self.entry_consulta.pack(side=tk.LEFT, expand=True, fill='x', ipady=12, padx=(0, 15))
        self.entry_consulta.bind("<Return>", lambda e: self.consultar_texto())
        
        btn_enviar = ttk.Button(frame_input, text="➤ Enviar", command=self.consultar_texto)
        btn_enviar.pack(side=tk.LEFT, padx=5)
        
        btn_voz = ttk.Button(frame_input, text="🎙️ Hablar", command=self.consultar_voz)
        btn_voz.pack(side=tk.LEFT, padx=5)
        
        self.agregar_mensaje("Asistente", "¡Hola! Soy tu asistente financiero local. Puedes preguntarme sobre bolsa, riesgo, ETFs, etc.\n", "bot")

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

    def configurar_ui_concepto(self, frame):
        ttk.Label(frame, text="Nuevo Concepto Financiero", style="Title.TLabel").pack(pady=(20, 10))
        ttk.Label(frame, text="Nombre del Concepto:", style="Card.TLabel").pack(pady=(10, 5))
        self.entry_nombre_concepto = tk.Entry(frame, width=60, font=FONT_MAIN, bg="#2A2A2A", fg=TEXT_COLOR, relief="flat")
        self.entry_nombre_concepto.pack(ipady=8)
        
        ttk.Label(frame, text="Definición exacta:", style="Card.TLabel").pack(pady=(20, 5))
        self.text_definicion = tk.Text(frame, height=5, width=60, font=FONT_MAIN, bg="#2A2A2A", fg=TEXT_COLOR, relief="flat")
        self.text_definicion.pack(pady=5)
        
        ttk.Button(frame, text="💾 Guardar Concepto", command=self.guardar_concepto).pack(pady=30)

    def configurar_ui_relacion(self, frame):
        ttk.Label(frame, text="Red Semántica", style="Title.TLabel").pack(pady=(20, 10))
        
        ttk.Label(frame, text="Concepto Origen:", style="Card.TLabel").pack(pady=(10, 5))
        self.entry_origen = tk.Entry(frame, width=50, font=FONT_MAIN, bg="#2A2A2A", fg=TEXT_COLOR, relief="flat")
        self.entry_origen.pack(ipady=8)
        
        ttk.Label(frame, text="Tipo de Relación (Ej. 'es un', 'reduce'):", style="Card.TLabel").pack(pady=(10, 5))
        self.entry_tipo_relacion = tk.Entry(frame, width=50, font=FONT_MAIN, bg="#2A2A2A", fg=TEXT_COLOR, relief="flat")
        self.entry_tipo_relacion.pack(ipady=8)
        
        ttk.Label(frame, text="Concepto Destino:", style="Card.TLabel").pack(pady=(10, 5))
        self.entry_destino = tk.Entry(frame, width=50, font=FONT_MAIN, bg="#2A2A2A", fg=TEXT_COLOR, relief="flat")
        self.entry_destino.pack(ipady=8)
        
        ttk.Button(frame, text="🔗 Conectar Conceptos", command=self.guardar_relacion).pack(pady=30)

    def configurar_ui_regla(self, frame):
        ttk.Label(frame, text="Motor de Inferencia (Reglas)", style="Title.TLabel").pack(pady=(20, 10))
        
        ttk.Label(frame, text="Condición (Keywords de usuario):", style="Card.TLabel").pack(pady=(10, 5))
        self.entry_condicion = tk.Entry(frame, width=60, font=FONT_MAIN, bg="#2A2A2A", fg=TEXT_COLOR, relief="flat")
        self.entry_condicion.pack(ipady=8)
        
        ttk.Label(frame, text="Conclusión a aplicar:", style="Card.TLabel").pack(pady=(10, 5))
        self.entry_conclusion = tk.Entry(frame, width=60, font=FONT_MAIN, bg="#2A2A2A", fg=TEXT_COLOR, relief="flat")
        self.entry_conclusion.pack(ipady=8)
        
        ttk.Button(frame, text="⚡ Añadir Regla", command=self.guardar_regla).pack(pady=30)

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
