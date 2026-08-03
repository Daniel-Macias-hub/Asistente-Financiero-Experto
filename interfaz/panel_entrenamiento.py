"""
Panel de Entrenamiento de la Base de Conocimiento.
Extraído de app.py para modularidad.
Contiene sub-pestañas para añadir conceptos, relaciones y reglas.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from entrenamiento.agregar_concepto import nuevo_concepto
from entrenamiento.agregar_relacion import nueva_relacion
from entrenamiento.agregar_regla import nueva_regla
from interfaz.estilos import (
    CARD_COLOR, TEXT_COLOR, FONT_MAIN, INPUT_BG
)


class PanelEntrenamiento:
    """Panel de la pestaña de entrenamiento con sub-tabs."""
    
    def __init__(self, parent_frame):
        """
        Args:
            parent_frame: Frame padre (pestaña del notebook).
        """
        self.frame = parent_frame
        self.crear_widgets()
        
    def crear_widgets(self):
        # Sub-pestañas
        sub_notebook = ttk.Notebook(self.frame)
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
        """Interfaz para agregar nuevos conceptos financieros."""
        ttk.Label(frame, text="Nuevo Concepto Financiero", style="Title.TLabel").pack(pady=(20, 10))
        ttk.Label(frame, text="Nombre del Concepto:", style="Card.TLabel").pack(pady=(10, 5))
        self.entry_nombre_concepto = tk.Entry(frame, width=60, font=FONT_MAIN, bg=INPUT_BG, fg=TEXT_COLOR, relief="flat")
        self.entry_nombre_concepto.pack(ipady=8)
        
        ttk.Label(frame, text="Definición exacta:", style="Card.TLabel").pack(pady=(20, 5))
        self.text_definicion = tk.Text(frame, height=5, width=60, font=FONT_MAIN, bg=INPUT_BG, fg=TEXT_COLOR, relief="flat")
        self.text_definicion.pack(pady=5)
        
        ttk.Button(frame, text="💾 Guardar Concepto", command=self.guardar_concepto).pack(pady=30)

    def configurar_ui_relacion(self, frame):
        """Interfaz para conectar conceptos con relaciones semánticas."""
        ttk.Label(frame, text="Red Semántica", style="Title.TLabel").pack(pady=(20, 10))
        
        ttk.Label(frame, text="Concepto Origen:", style="Card.TLabel").pack(pady=(10, 5))
        self.entry_origen = tk.Entry(frame, width=50, font=FONT_MAIN, bg=INPUT_BG, fg=TEXT_COLOR, relief="flat")
        self.entry_origen.pack(ipady=8)
        
        ttk.Label(frame, text="Tipo de Relación (Ej. 'es un', 'reduce'):", style="Card.TLabel").pack(pady=(10, 5))
        self.entry_tipo_relacion = tk.Entry(frame, width=50, font=FONT_MAIN, bg=INPUT_BG, fg=TEXT_COLOR, relief="flat")
        self.entry_tipo_relacion.pack(ipady=8)
        
        ttk.Label(frame, text="Concepto Destino:", style="Card.TLabel").pack(pady=(10, 5))
        self.entry_destino = tk.Entry(frame, width=50, font=FONT_MAIN, bg=INPUT_BG, fg=TEXT_COLOR, relief="flat")
        self.entry_destino.pack(ipady=8)
        
        ttk.Button(frame, text="🔗 Conectar Conceptos", command=self.guardar_relacion).pack(pady=30)

    def configurar_ui_regla(self, frame):
        """Interfaz para agregar reglas de inferencia al motor experto."""
        ttk.Label(frame, text="Motor de Inferencia (Reglas)", style="Title.TLabel").pack(pady=(20, 10))
        
        ttk.Label(frame, text="Condición (Keywords de usuario):", style="Card.TLabel").pack(pady=(10, 5))
        self.entry_condicion = tk.Entry(frame, width=60, font=FONT_MAIN, bg=INPUT_BG, fg=TEXT_COLOR, relief="flat")
        self.entry_condicion.pack(ipady=8)
        
        ttk.Label(frame, text="Conclusión a aplicar:", style="Card.TLabel").pack(pady=(10, 5))
        self.entry_conclusion = tk.Entry(frame, width=60, font=FONT_MAIN, bg=INPUT_BG, fg=TEXT_COLOR, relief="flat")
        self.entry_conclusion.pack(ipady=8)
        
        ttk.Button(frame, text="⚡ Añadir Regla", command=self.guardar_regla).pack(pady=30)

    # --- Acciones de guardado ---
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
