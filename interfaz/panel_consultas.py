"""
Panel de Consultas y Asesoría Financiera.
Extraído de app.py para modularidad.
Contiene el historial de chat, entrada de texto y botones de voz.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading

from experto.motor import procesar_consulta
from audio.tts import hablar
from audio.stt import escuchar
from interfaz.estilos import (
    BG_COLOR, CARD_COLOR, TEXT_COLOR, MUTED_TEXT, ACCENT_COLOR,
    FONT_MAIN, FONT_CODE, INPUT_BG
)


class PanelConsultas:
    """Panel de la pestaña de consultas con historial tipo chat."""
    
    def __init__(self, parent_frame, root):
        """
        Args:
            parent_frame: Frame padre (pestaña del notebook).
            root: Ventana raíz de Tkinter (para root.after).
        """
        self.root = root
        self.frame = parent_frame
        self.crear_widgets()
        
    def crear_widgets(self):
        # Contenedor principal de consulta
        container = ttk.Frame(self.frame, style="Card.TFrame")
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
            frame_input, font=FONT_MAIN, bg=INPUT_BG, fg=TEXT_COLOR, 
            insertbackground=TEXT_COLOR, relief="flat"
        )
        self.entry_consulta.pack(side=tk.LEFT, expand=True, fill='x', ipady=12, padx=(0, 15))
        self.entry_consulta.bind("<Return>", lambda e: self.consultar_texto())
        
        btn_enviar = ttk.Button(frame_input, text="➤ Enviar", command=self.consultar_texto)
        btn_enviar.pack(side=tk.LEFT, padx=5)
        
        btn_voz = ttk.Button(frame_input, text="🎙️ Hablar", command=self.consultar_voz)
        btn_voz.pack(side=tk.LEFT, padx=5)
        
        self.agregar_mensaje("Asistente", "¡Hola! Soy tu asistente financiero local. Puedes preguntarme sobre bolsa, riesgo, ETFs, criptomonedas y más.\n", "bot")

    def agregar_mensaje(self, autor, texto, tag):
        """Agrega un mensaje al historial con formato de chat."""
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
        """Procesa una consulta de texto a través del motor experto."""
        self.agregar_mensaje("Usuario", texto_usuario, "user")
        
        respuesta, log_inferencia = procesar_consulta(texto_usuario)
        
        for l in log_inferencia:
            self.agregar_mensaje("Log", l, "log")
            
        self.agregar_mensaje("Asistente", respuesta, "bot")
        
        # Reproducir voz en hilo separado
        threading.Thread(target=hablar, args=(respuesta,), daemon=True).start()
        
    def consultar_texto(self):
        """Maneja consulta por entrada de texto."""
        texto = self.entry_consulta.get().strip()
        if not texto:
            return
        self.entry_consulta.delete(0, tk.END)
        self.procesar_respuesta(texto)
        
    def consultar_voz(self):
        """Maneja consulta por voz usando el micrófono INMP441 si el ESP32 está conectado."""
        from comunicacion_esp32 import esp32_comm
        from audio.stt import escuchar_desde_pcm
        
        if esp32_comm.conectado:
            self.agregar_mensaje("Log", "🎙️ Escuchando desde el micrófono INMP441 (4s)...", "log")
            self.root.update()

            def hilo_voz_esp():
                esp32_comm.enviar_comando_oled("ESCUCHANDO")
                metrics, res = esp32_comm.capturar_audio_mic(4)
                esp32_comm.enviar_comando_oled("PROCESANDO")
                if metrics and "pcm_bytes" in metrics:
                    texto = escuchar_desde_pcm(metrics["pcm_bytes"])
                    if texto and not texto.startswith("Error"):
                        self.root.after(0, self.procesar_respuesta, texto)
                    else:
                        self.agregar_mensaje("Log", f"STT: {texto}", "log")
                        esp32_comm.enviar_comando_oled("ERROR")
                else:
                    self.agregar_mensaje("Log", "No se recibió audio del micrófono INMP441.", "log")
                    esp32_comm.enviar_comando_oled("ERROR")

            threading.Thread(target=hilo_voz_esp, daemon=True).start()
        else:
            self.agregar_mensaje("Log", "Escuchando desde micrófono local de la PC...", "log")
            self.root.update()

            def hilo_voz_pc():
                texto_reconocido = escuchar()
                if "Error" in texto_reconocido:
                    self.agregar_mensaje("Log", texto_reconocido, "log")
                else:
                    self.root.after(0, self.procesar_respuesta, texto_reconocido)

            threading.Thread(target=hilo_voz_pc, daemon=True).start()

