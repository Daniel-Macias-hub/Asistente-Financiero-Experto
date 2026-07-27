"""
Interfaz Gráfica Rediseñada (Tkinter) - Asistente Financiero Experto
Dashboard Profesional Estilo Centro de Operaciones (feature/ui-redesign)
Fondo Slate Dark, Tipografías 14-28px, Previsualización Embebida de Cámara (PIL) y Chat ChatGPT.
"""
import os
import sys
import time
import threading
import requests
import cv2
import numpy as np
from PIL import Image, ImageTk

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# UTF-8 stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from experto.motor import procesar_consulta
from experto.finanzas_tiempo_real import obtener_datos_accion, generar_respuesta_precio
from entrenamiento.agregar_concepto import nuevo_concepto
from entrenamiento.agregar_relacion import nueva_relacion
from entrenamiento.agregar_regla import nueva_regla
from audio.tts import hablar, detener_habla
from audio.stt import escuchar_desde_pcm
from conocimiento.database import get_connection
from comunicacion_esp32 import esp32_comm
from vision.detector_logo import DetectorCriptoUnificado

# Paleta de Colores Profesional Slate/Esmeralda
BG_MAIN     = "#0E1117"  # Slate muy oscuro
BG_CARD     = "#161B22"  # Tarjeta oscura
BG_ENTRY    = "#21262D"  # Campo de texto
TEXT_MAIN   = "#F0F6FC"  # Texto principal claro
TEXT_MUTED  = "#8B949E"  # Texto secundario
CLR_GREEN   = "#00D287"  # Verde esmeralda (Estados OK)
CLR_CYAN    = "#00B4D8"  # Azul cian (Info)
CLR_AMBER   = "#FFB703"  # Ámbar (Procesando)
CLR_RED     = "#FF4D4D"  # Rojo carmesí (Error)

FONT_TITLE  = ("Segoe UI", 22, "bold")
FONT_SUB    = ("Segoe UI", 16, "bold")
FONT_CARD   = ("Segoe UI", 13, "bold")
FONT_BODY   = ("Segoe UI", 11)
FONT_CODE   = ("Consolas", 10)

class AsistenteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Asistente Experto Financiero — Dashboard de Operaciones")
        self.root.geometry("1280x850")
        self.root.minsize(1024, 720)
        self.root.configure(bg=BG_MAIN)

        self.cam_img_tk = None
        self.cam_hd_tk = None
        self.ultimo_frame_cv2 = None
        self.stream_activo = False
        self.flash_encendido = False
        self.window_agrandar = None
        self.canvas_agrandar = None
        self.configurar_estilos()
        self.crear_widgets()

    def configurar_estilos(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TNotebook", background=BG_MAIN, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=BG_CARD, foreground=TEXT_MAIN, padding=[16, 10], font=("Segoe UI", 11, "bold"))
        self.style.map("TNotebook.Tab", background=[("selected", CLR_GREEN)], foreground=[("selected", "#000000")])
        self.style.configure("TFrame", background=BG_MAIN)
        self.style.configure("Card.TFrame", background=BG_CARD)
        self.style.configure("TLabel", background=BG_MAIN, foreground=TEXT_MAIN, font=FONT_BODY)
        self.style.configure("Card.TLabel", background=BG_CARD, foreground=TEXT_MAIN, font=FONT_BODY)
        self.style.configure("Title.TLabel", background=BG_CARD, foreground=CLR_GREEN, font=FONT_TITLE)
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"), background=CLR_GREEN, foreground="#000000", padding=8)
        self.style.map("TButton", background=[("active", "#00A96B")])

    def crear_widgets(self):
        # 1. Cabecera Dashboard
        header = ttk.Frame(self.root, style="Card.TFrame")
        header.pack(fill='x', padx=15, pady=(10, 5))

        top_bar = ttk.Frame(header, style="Card.TFrame")
        top_bar.pack(fill='x', padx=15, pady=10)

        ttk.Label(top_bar, text="🧠 ASISTENTE EDUCATIVO FINANCIERO", style="Title.TLabel").pack(side=tk.LEFT)
        
        # Indicadores Globales Vivos
        ind_bar = ttk.Frame(top_bar, style="Card.TFrame")
        ind_bar.pack(side=tk.RIGHT)

        self.lbl_ind_esp = ttk.Label(ind_bar, text="🔴 ESP32-S3", font=("Segoe UI", 10, "bold"), foreground=CLR_RED)
        self.lbl_ind_esp.pack(side=tk.LEFT, padx=8)

        self.lbl_ind_cam = ttk.Label(ind_bar, text="🔴 ESP32-CAM", font=("Segoe UI", 10, "bold"), foreground=CLR_RED)
        self.lbl_ind_cam.pack(side=tk.LEFT, padx=8)

        self.lbl_ind_api = ttk.Label(ind_bar, text="🟢 APIs", font=("Segoe UI", 10, "bold"), foreground=CLR_GREEN)
        self.lbl_ind_api.pack(side=tk.LEFT, padx=8)

        self.lbl_ind_ia  = ttk.Label(ind_bar, text="🟢 Visión IA", font=("Segoe UI", 10, "bold"), foreground=CLR_GREEN)
        self.lbl_ind_ia.pack(side=tk.LEFT, padx=8)

        # 2. Notebook Principal
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=15, pady=5)

        self.tab_dashboard     = ttk.Frame(self.notebook, style="TFrame")
        self.tab_chat          = ttk.Frame(self.notebook, style="TFrame")
        self.tab_mercado       = ttk.Frame(self.notebook, style="TFrame")
        self.tab_entrenamiento = ttk.Frame(self.notebook, style="TFrame")
        self.tab_conocimiento  = ttk.Frame(self.notebook, style="TFrame")

        self.notebook.add(self.tab_dashboard, text="🎛️ Dashboard & Operaciones")
        self.notebook.add(self.tab_chat, text="💬 Chat Conversacional")
        self.notebook.add(self.tab_mercado, text="📈 Mercado en Tiempo Real")
        self.notebook.add(self.tab_entrenamiento, text="⚙️ Entrenamiento Base")
        self.notebook.add(self.tab_conocimiento, text="📚 Base de Conocimiento")

        self.configurar_tab_dashboard()
        self.configurar_tab_chat()
        self.configurar_tab_mercado()
        self.configurar_tab_entrenamiento()
        self.configurar_tab_conocimiento()

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

    # --------------------------------------------------------------------------
    # TAB 1: DASHBOARD DE OPERACIONES (PREVISUALIZACIÓN EMBEBIDA + CARDS)
    # --------------------------------------------------------------------------
    def configurar_tab_dashboard(self):
        container = ttk.Frame(self.tab_dashboard, style="TFrame")
        container.pack(expand=True, fill='both', padx=5, pady=5)

        # Split Superior: Cards a la Izquierda / Cámara Embebida a la Derecha
        pan_top = ttk.Frame(container, style="TFrame")
        pan_top.pack(fill='x', pady=(0, 5))

        # --- Panel Izquierdo: Tarjetas de Dispositivo ---
        card_panel = ttk.Frame(pan_top, style="TFrame")
        card_panel.pack(side=tk.LEFT, expand=True, fill='both', padx=(0, 5))

        # Tarjeta 1: ESP32-S3
        c_esp = ttk.Frame(card_panel, style="Card.TFrame")
        c_esp.pack(fill='x', pady=4, ipady=5)

        ttk.Label(c_esp, text="🖥️ ESP32-S3 (Interfaz Física)", font=FONT_CARD, foreground=CLR_CYAN).pack(anchor='w', padx=12, pady=(8, 2))

        f_port = ttk.Frame(c_esp, style="Card.TFrame")
        f_port.pack(fill='x', padx=12, pady=2)
        ttk.Label(f_port, text="Puerto: ", font=FONT_BODY).pack(side=tk.LEFT)
        self.combo_puertos = ttk.Combobox(f_port, values=esp32_comm.obtener_puertos_disponibles(), state="readonly", width=10)
        self.combo_puertos.pack(side=tk.LEFT, padx=5)
        if self.combo_puertos['values']:
            self.combo_puertos.current(0)
        ttk.Button(f_port, text="🔄 Puertos", command=self.actualizar_lista_puertos).pack(side=tk.LEFT, padx=4)
        ttk.Button(f_port, text="🔌 Conectar", command=self.conectar_esp32_dinamico).pack(side=tk.LEFT, padx=4)

        self.lbl_status_esp32 = ttk.Label(c_esp, text="Estado: 🔴 DESCONECTADO", font=("Segoe UI", 10, "bold"), foreground=CLR_RED)
        self.lbl_status_esp32.pack(anchor='w', padx=12, pady=2)

        f_btns_esp = ttk.Frame(c_esp, style="Card.TFrame")
        f_btns_esp.pack(fill='x', padx=12, pady=6)
        ttk.Button(f_btns_esp, text="📺 Test OLED", command=self.probar_oled_real).pack(side=tk.LEFT, padx=2)
        ttk.Button(f_btns_esp, text="🔊 Test Audio", command=self.probar_audio_real).pack(side=tk.LEFT, padx=2)
        ttk.Button(f_btns_esp, text="🎙️ Test Mic", command=self.probar_mic_real).pack(side=tk.LEFT, padx=2)

        # Tarjeta 2: ESP32-CAM
        c_cam = ttk.Frame(card_panel, style="Card.TFrame")
        c_cam.pack(fill='x', pady=4, ipady=5)

        ttk.Label(c_cam, text="📷 ESP32-CAM (Visión Remota)", font=FONT_CARD, foreground=CLR_CYAN).pack(anchor='w', padx=12, pady=(8, 2))

        f_ip = ttk.Frame(c_cam, style="Card.TFrame")
        f_ip.pack(fill='x', padx=12, pady=2)
        ttk.Label(f_ip, text="IP Cámara: ", font=FONT_BODY).pack(side=tk.LEFT)
        self.entry_ip_cam = ttk.Entry(f_ip, width=22)
        self.entry_ip_cam.insert(0, "http://192.168.3.135")
        self.entry_ip_cam.pack(side=tk.LEFT, padx=5)
        ttk.Label(f_ip, text="(sólo IP base, sin /capture ni /stream)",
                  font=("Segoe UI", 9), foreground=TEXT_MUTED).pack(side=tk.LEFT, padx=2)

        self.lbl_status_cam = ttk.Label(c_cam, text="Estado: 🔴 DESCONOCIDO", font=("Segoe UI", 10, "bold"), foreground=TEXT_MUTED)
        self.lbl_status_cam.pack(anchor='w', padx=12, pady=2)

        f_btns_cam = ttk.Frame(c_cam, style="Card.TFrame")
        f_btns_cam.pack(fill='x', padx=12, pady=6)
        ttk.Button(f_btns_cam, text="📷 Foto", command=self.probar_camara_real).pack(side=tk.LEFT, padx=2)
        self.btn_stream = ttk.Button(f_btns_cam, text="📹 Video en Vivo", command=self.toggle_video_stream)
        self.btn_stream.pack(side=tk.LEFT, padx=2)
        self.btn_flash = ttk.Button(f_btns_cam, text="💡 Flash: OFF", command=self.toggle_flash_led)
        self.btn_flash.pack(side=tk.LEFT, padx=2)
        ttk.Button(f_btns_cam, text="🔍 Agrandar (HD)", command=self.abrir_visor_agrandado).pack(side=tk.LEFT, padx=2)
        ttk.Button(f_btns_cam, text="📸 Escanear Cripto", command=self.escanear_cripto_pipeline).pack(side=tk.LEFT, padx=2)

        # --- Panel Derecho: Visor de Cámara Embebido en Canvas ---
        c_visor = ttk.Frame(pan_top, style="Card.TFrame")
        c_visor.pack(side=tk.RIGHT, fill='both', padx=(5, 0))

        ttk.Label(c_visor, text="📡 VISTA PREVIA CÁMARA (EMBEBIDA)", font=FONT_CARD, foreground=CLR_GREEN).pack(anchor='w', padx=12, pady=(8, 4))

        self.canvas_cam = tk.Canvas(c_visor, width=400, height=266, bg="#000000", highlightthickness=1, highlightbackground=CLR_GREEN)
        self.canvas_cam.pack(padx=12, pady=4)
        self.canvas_cam.create_text(200, 133, text="Esperando captura...", fill=TEXT_MUTED, font=FONT_BODY)

        self.lbl_metrics_cam = ttk.Label(c_visor, text="Resolución: N/A | Tamaño: N/A | Latencia: N/A", font=("Consolas", 9), foreground=CLR_CYAN)
        self.lbl_metrics_cam.pack(anchor='w', padx=12, pady=(4, 8))

        # Split Inferior: Consola de Trazabilidad Serial TX ➔ / RX ◄
        c_console = ttk.Frame(container, style="Card.TFrame")
        c_console.pack(expand=True, fill='both', pady=(5, 0))

        ttk.Label(c_console, text="📜 REGISTRO DE TRAZABILIDAD SERIAL Y COMUNICACIÓN (TX ➔ / RX ◄)", font=FONT_CARD, foreground=TEXT_MAIN).pack(anchor='w', padx=12, pady=(6, 2))

        self.log_console = scrolledtext.ScrolledText(c_console, state='disabled', wrap=tk.WORD, font=FONT_CODE, bg=BG_ENTRY, fg=TEXT_MAIN, height=8)
        self.log_console.pack(expand=True, fill='both', padx=12, pady=(2, 8))

        esp32_comm.callback_log = self.agregar_log_consola
        self.agregar_log_consola("[SISTEMA] Dashboard listo. Conecta el ESP32-S3 en el puerto COM correspondiente.")

    def agregar_log_consola(self, msg):
        ts = time.strftime("[%H:%M:%S] ")
        def _append():
            self.log_console.configure(state='normal')
            self.log_console.insert(tk.END, ts + msg + "\n")
            self.log_console.see(tk.END)
            self.log_console.configure(state='disabled')
        self.root.after(0, _append)

    def actualizar_lista_puertos(self):
        puertos = esp32_comm.obtener_puertos_disponibles()
        self.combo_puertos['values'] = puertos
        
        # Preferir COM5 o cualquier puerto distinto a COM4 (ESP32-CAM)
        puertos_s3 = [p for p in puertos if p != "COM4"]
        
        if "COM5" in puertos:
            self.combo_puertos.set("COM5")
        elif puertos_s3:
            self.combo_puertos.set(puertos_s3[0])
        elif puertos:
            self.combo_puertos.current(0)
            
        self.agregar_log_consola(f"[PUERTOS] Lista de puertos del sistema actualizada: {puertos}")

    def conectar_esp32_dinamico(self):
        puerto_sel = self.combo_puertos.get()

        def _run():
            self.agregar_log_consola(f"[CONEXIÓN] Intentando conectar a {puerto_sel} (ESP32-S3)...")
            exito, puerto_ok = esp32_comm.conectar(puerto_sel)
            
            # Si el puerto seleccionado falló, probar automáticamente todos los demás puertos disponibles
            if not exito:
                puertos_disp = esp32_comm.obtener_puertos_disponibles()
                for p_alt in puertos_disp:
                    if p_alt != puerto_sel:
                        self.agregar_log_consola(f"[AUTO-BUSQUEDA] Probando puerto alternativo {p_alt}...")
                        exito_alt, puerto_ok_alt = esp32_comm.conectar(p_alt)
                        if exito_alt:
                            exito = True
                            puerto_ok = puerto_ok_alt
                            break

            if exito and puerto_ok:
                def _gui_ok():
                    self.combo_puertos.set(puerto_ok)
                    self.lbl_status_esp32.configure(text=f"Estado: 🟢 CONECTADO ({puerto_ok})", foreground=CLR_GREEN)
                    self.lbl_ind_esp.configure(text=f"🟢 ESP32-S3 ({puerto_ok})", foreground=CLR_GREEN)
                self.root.after(0, _gui_ok)
                esp32_comm.enviar_comando_oled("IDLE")
                self.agregar_log_consola(f"[CONEXIÓN] ✓ Conexión física verificada en {puerto_ok}.")
            else:
                def _gui_fail():
                    self.lbl_status_esp32.configure(text="Estado: 🔴 DESCONECTADO", foreground=CLR_RED)
                    self.lbl_ind_esp.configure(text="🔴 ESP32-S3", foreground=CLR_RED)
                self.root.after(0, _gui_fail)
                self.agregar_log_consola("[CONEXIÓN HINT] Si el puerto está retenido por otro programa o Thonny, desconecta y vuelve a conectar el cable USB del ESP32-S3.")

        threading.Thread(target=_run, daemon=True).start()

    def probar_oled_real(self):
        def _run():
            self.agregar_log_consola("[TEST OLED] Solicitando secuencia de animaciones...")
            exito, res = esp32_comm.ejecutar_test_oled()
            if exito and "OLED_TEST_OK" in res:
                self.agregar_log_consola("[TEST OLED] ✓ OLED_TEST_OK recibido.")
            else:
                self.agregar_log_consola(f"[TEST OLED] ✗ Fallo: {res}")
        threading.Thread(target=_run, daemon=True).start()

    def probar_audio_real(self):
        def _run():
            self.agregar_log_consola("[TEST AUDIO] Solicitando tono 440Hz por MAX98357A + Bocina...")
            exito, res = esp32_comm.ejecutar_test_audio()
            if exito and "AUDIO_TEST_OK" in res:
                self.agregar_log_consola("[TEST AUDIO] ✓ AUDIO_TEST_OK recibido.")
            else:
                self.agregar_log_consola(f"[TEST AUDIO] ✗ Fallo: {res}")
        threading.Thread(target=_run, daemon=True).start()

    def probar_mic_real(self):
        def _run():
            self.agregar_log_consola("[TEST MIC] Grabando 4s desde INMP441 por I2S 0 RX...")
            metrics, res = esp32_comm.capturar_audio_mic(4)
            if metrics and metrics.get("rms", 0) > 0:
                rms = metrics["rms"]
                dur = metrics["duracion"]
                pcm_bytes = metrics.get("pcm_bytes")
                self.agregar_log_consola(f"[TEST MIC] ✓ MIC_TEST_OK: Duración={dur:.1f}s, RMS={rms:.1f}")
                if pcm_bytes:
                    self.agregar_log_consola("[TEST MIC] 🔊 Reproduciendo tu voz grabada directamente en la bocina física MAX98357A...")
                    esp32_comm.reproducir_audio_bocina_pcm(pcm_bytes)
            else:
                self.agregar_log_consola(f"[TEST MIC] ✗ Fallo: {res}")
        threading.Thread(target=_run, daemon=True).start()

    def probar_camara_real(self):
        """Captura una foto (con o sin stream activo) y la muestra en el Dashboard + popup."""
        def _run():
            img = None
            # Si el stream está activo, tomar el último frame de RAM (sin HTTP)
            if self.stream_activo and self.ultimo_frame_cv2 is not None:
                img = self.ultimo_frame_cv2.copy()
                w, h = img.shape[1], img.shape[0]
                t_trans = 0.0
                size_kb = 0.0
                self.agregar_log_consola("[CÁMARA] ✓ Foto capturada desde frame en RAM (stream activo)")
            else:
                # Sin stream: petición HTTP a /capture
                _, capture_url, _ = self._get_cam_urls()
                self.agregar_log_consola(f"[CÁMARA] Solicitando fotograma a {capture_url}...")
                t0 = time.time()
                try:
                    r = requests.get(capture_url, timeout=6)
                    t_trans = (time.time() - t0) * 1000
                    if r.status_code == 200:
                        arr = np.frombuffer(r.content, np.uint8)
                        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                        if img is not None:
                            h, w, _ = img.shape
                            size_kb = len(r.content) / 1024.0
                            self.agregar_log_consola(
                                f"[CÁMARA] ✓ Fotograma recibido: {w}x{h} px, {size_kb:.1f} KB, {t_trans:.0f} ms")
                    else:
                        self.agregar_log_consola(f"[CÁMARA] ✗ HTTP {r.status_code}")
                except Exception as e:
                    self.agregar_log_consola(f"[CÁMARA] ✗ Error: {e}")

            if img is not None:
                self.ultimo_frame_cv2 = img
                h, w, _ = img.shape
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                # Actualizar canvas pequeño del Dashboard
                img_pil_small = Image.fromarray(img_rgb).resize((400, 266), Image.Resampling.LANCZOS)
                self.cam_img_tk = ImageTk.PhotoImage(img_pil_small)
                def _render_dash():
                    self.canvas_cam.delete("all")
                    self.canvas_cam.create_image(0, 0, image=self.cam_img_tk, anchor='nw')
                    self.lbl_metrics_cam.configure(
                        text=f"Res: {w}x{h} px | FPS: FOTO")
                    self.lbl_status_cam.configure(
                        text=f"Estado: 🟢 Foto capturada ({w}x{h})", foreground=CLR_GREEN)
                    self.lbl_ind_cam.configure(text="🟢 ESP32-CAM", foreground=CLR_GREEN)
                self.root.after(0, _render_dash)
                # Mostrar foto en panel HD o en popup si el HD no está abierto
                self.root.after(0, lambda i=img: self._mostrar_foto_panel(i))

        threading.Thread(target=_run, daemon=True).start()


    def toggle_video_stream(self):
        """Activa o desactiva la transmisión MJPEG en tiempo real de la ESP32-CAM."""
        if self.stream_activo:
            self.stream_activo = False
            try:
                self.btn_stream.configure(text="📹 Video en Vivo")
            except Exception:
                pass
            self.agregar_log_consola("[CÁMARA] Transmisión de video detenida.")
        else:
            self.stream_activo = True
            try:
                self.btn_stream.configure(text="⏹️ Detener Video")
            except Exception:
                pass
            self.agregar_log_consola("[CÁMARA] Iniciando transmisión MJPEG en tiempo real...")
            threading.Thread(target=self._bucle_video_stream, daemon=True).start()
            # Si la ventana HD está abierta, lanzar bucle HD dedicado
            if self.window_agrandar and self.window_agrandar.winfo_exists():
                threading.Thread(target=self._bucle_hd_canvas, daemon=True).start()

    def _get_cam_urls(self):
        """Deriva stream_url y capture_url a partir de la IP base en el campo de texto."""
        raw = self.entry_ip_cam.get().strip().rstrip("/")
        # Eliminar cualquier endpoint que ya venga en la URL
        base = raw.replace("/capture", "").replace("/stream", "").replace("/led", "")
        return f"{base}/stream", f"{base}/capture", base

    def toggle_flash_led(self):
        """Conmuta el LED Flash enviando solo un HTTP GET /led — NO interrumpe el stream."""
        self.flash_encendido = not self.flash_encendido
        nuevo_estado = 1 if self.flash_encendido else 0
        txt = "💡 Flash: ON" if self.flash_encendido else "💡 Flash: OFF"
        try:
            self.btn_flash.configure(text=txt)
        except Exception:
            pass
        self.agregar_log_consola(
            f"[FLASH LED] Luz LED {'ENCENDIDA (SÓLIDA)' if self.flash_encendido else 'APAGADA'}.")

        _, _, base = self._get_cam_urls()
        led_url = f"{base}/led?state={nuevo_estado}"

    def _get_cam_urls(self):
        """Deriva stream_url y capture_url a partir de la IP base en el campo de texto."""
        raw = self.entry_ip_cam.get().strip().rstrip("/")
        base = raw.replace("/capture", "").replace("/stream", "").replace("/led", "")
        return f"{base}/stream", f"{base}/capture", base

    def toggle_flash_led(self):
        """Conmuta el LED Flash. Si el stream está activo, lo reinicia limpiamente (<400ms)."""
        self.flash_encendido = not self.flash_encendido
        nuevo_estado = 1 if self.flash_encendido else 0
        txt = "💡 Flash: ON" if self.flash_encendido else "💡 Flash: OFF"
        try:
            self.btn_flash.configure(text=txt)
        except Exception:
            pass
        self.agregar_log_consola(
            f"[FLASH LED] Luz LED {'ENCENDIDA (SÓLIDA)' if self.flash_encendido else 'APAGADA'}.")

        _, _, base = self._get_cam_urls()
        led_url = f"{base}/led?state={nuevo_estado}"

        if self.stream_activo:
            # Reinicio limpio: parar → LED → reiniciar (todo en hilo, <400ms)
            def _restart_with_led():
                self.stream_activo = False
                time.sleep(0.15)
                try:
                    requests.get(led_url, timeout=1)
                except Exception:
                    pass
                time.sleep(0.1)
                self.stream_activo = True
                try:
                    self.btn_stream.configure(text="⏹️ Detener Video")
                except Exception:
                    pass
                threading.Thread(target=self._bucle_video_stream, daemon=True).start()
                if self.window_agrandar and self.window_agrandar.winfo_exists():
                    threading.Thread(target=self._bucle_hd_canvas, daemon=True).start()
            threading.Thread(target=_restart_with_led, daemon=True).start()
        else:
            def _send_led():
                try:
                    requests.get(led_url, timeout=2)
                except Exception:
                    pass
            threading.Thread(target=_send_led, daemon=True).start()


    def abrir_visor_agrandado(self):
        """Ventana HD con stream + panel lateral de foto integrado (sin popups extra)."""
        if self.window_agrandar and self.window_agrandar.winfo_exists():
            self.window_agrandar.lift()
            return

        self.window_agrandar = tk.Toplevel(self.root)
        self.window_agrandar.title("📡 VISUALIZADOR DE CÁMARA HD")
        self.window_agrandar.geometry("1200x720")
        self.window_agrandar.resizable(True, True)
        self.window_agrandar.configure(bg=BG_MAIN)
        self.panel_foto_hd = None  # Panel lateral de foto, inicialmente oculto

        ttk.Label(
            self.window_agrandar,
            text="📡 VISUALIZADOR DE CÁMARA HD (TIEMPO REAL)",
            font=FONT_SUB, foreground=CLR_GREEN
        ).pack(side=tk.TOP, pady=(6, 2))

        # ── Barra de Control (5 botones) ───────────────────────────────────────────────
        f_hd_ctrl = ttk.Frame(self.window_agrandar, style="Card.TFrame")
        f_hd_ctrl.pack(side=tk.TOP, fill='x', padx=10, pady=4)

        ttk.Button(f_hd_ctrl, text="📸 Foto HD",
                   command=self._foto_hd).pack(side=tk.LEFT, padx=6)
        ttk.Button(f_hd_ctrl, text="📹 Video en Vivo",
                   command=self.toggle_video_stream).pack(side=tk.LEFT, padx=6)
        ttk.Button(f_hd_ctrl, text="⚡ Flash ON/OFF",
                   command=self.toggle_flash_led).pack(side=tk.LEFT, padx=6)
        ttk.Button(f_hd_ctrl, text="📷 Escanear Cripto",
                   command=self.escanear_cripto_pipeline).pack(side=tk.LEFT, padx=6)
        ttk.Button(f_hd_ctrl, text="❌ Cerrar",
                   command=self.window_agrandar.destroy).pack(side=tk.RIGHT, padx=6)

        # ── Área principal (stream + panel foto lado a lado) ───────────────────────────────
        self.frame_hd_principal = ttk.Frame(self.window_agrandar, style="TFrame")
        self.frame_hd_principal.pack(side=tk.TOP, expand=True, fill='both', padx=10, pady=(0, 10))

        # Canvas de stream (ocupa todo el ancho por defecto)
        self.canvas_agrandar = tk.Canvas(
            self.frame_hd_principal, bg="#000000",
            highlightthickness=2, highlightbackground=CLR_GREEN
        )
        self.canvas_agrandar.pack(side=tk.LEFT, expand=True, fill='both')

        # Mostrar frame en RAM de inmediato si existe
        if self.ultimo_frame_cv2 is not None:
            self._renderizar_frame_hd(self.ultimo_frame_cv2)
        else:
            self.canvas_agrandar.create_text(
                400, 300,
                text="Presiona 'Video en Vivo' o 'Foto HD' para iniciar",
                fill=TEXT_MUTED, font=FONT_BODY
            )

        # Lanzar bucle HD si el stream ya está corriendo
        if self.stream_activo:
            threading.Thread(target=self._bucle_hd_canvas, daemon=True).start()


    # ── Helpers del Visor HD ─────────────────────────────────────────────────

    def _mostrar_foto_panel(self, img_bgr):
        """
        Muestra la foto capturada:
        - En el panel lateral de la ventana HD (si está abierta) → SIN nueva ventana
        - En un Toplevel pequeño (si solo está en el Dashboard)
        """
        h, w, _ = img_bgr.shape
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

        if self.window_agrandar and self.window_agrandar.winfo_exists():
            # ─ Panel lateral integrado dentro de la ventana HD ──────────────────────
            if self.panel_foto_hd is None or not self.panel_foto_hd.winfo_exists():
                # Crear panel lateral si no existe
                self.panel_foto_hd = ttk.Frame(
                    self.frame_hd_principal, style="Card.TFrame", width=340)
                self.panel_foto_hd.pack(side=tk.RIGHT, fill='y', padx=(6, 0))
                self.panel_foto_hd.pack_propagate(False)

                ttk.Label(
                    self.panel_foto_hd,
                    text="📸 Última Foto Capturada",
                    font=FONT_CARD, foreground=CLR_AMBER
                ).pack(pady=(8, 4))

                self._lbl_foto_panel = tk.Label(
                    self.panel_foto_hd, bg="#000000", cursor="hand2")
                self._lbl_foto_panel.pack(padx=8, pady=4)

                self._lbl_info_foto = ttk.Label(
                    self.panel_foto_hd, text="", font=("Consolas", 8),
                    foreground=CLR_CYAN)
                self._lbl_info_foto.pack(pady=(0, 4))

                f_foto_btns = ttk.Frame(self.panel_foto_hd, style="Card.TFrame")
                f_foto_btns.pack(fill='x', padx=8, pady=4)

                ttk.Button(
                    f_foto_btns, text="💾 Guardar PNG",
                    command=lambda: self._guardar_foto_png(self.ultimo_frame_cv2)
                ).pack(fill='x', pady=2)
                ttk.Button(
                    f_foto_btns, text="📷 Escanear Cripto",
                    command=self.escanear_cripto_pipeline
                ).pack(fill='x', pady=2)
                ttk.Button(
                    f_foto_btns, text="✖ Cerrar Panel Foto",
                    command=self._cerrar_panel_foto
                ).pack(fill='x', pady=2)

            # Actualizar imagen en el panel (escalar a 320x220)
            img_thumb = Image.fromarray(img_rgb)
            img_thumb.thumbnail((320, 220), Image.Resampling.LANCZOS)
            self._foto_panel_tk = ImageTk.PhotoImage(img_thumb)
            self._lbl_foto_panel.configure(image=self._foto_panel_tk)
            self._lbl_info_foto.configure(text=f"{w}x{h} px")

        else:
            # ─ Popup pequeño solo si la ventana HD NO está abierta (Dashboard) ──
            img_popup = Image.fromarray(img_rgb)
            img_popup.thumbnail((480, 360), Image.Resampling.LANCZOS)
            popup = tk.Toplevel(self.root)
            popup.title(f"📸 Foto Capturada — {w}x{h} px")
            popup.configure(bg=BG_MAIN)
            popup.resizable(False, False)
            tk_img = ImageTk.PhotoImage(img_popup)
            lbl = tk.Label(popup, image=tk_img, bg="#000000")
            lbl.image = tk_img
            lbl.pack(padx=6, pady=6)
            ttk.Label(popup, text=f"{w}x{h} px",
                      font=("Consolas", 9), foreground=CLR_CYAN).pack(pady=(0, 2))
            f_b = ttk.Frame(popup, style="Card.TFrame")
            f_b.pack(fill='x', padx=6, pady=4)
            ttk.Button(f_b, text="💾 Guardar PNG",
                       command=lambda: self._guardar_foto_png(img_bgr)).pack(side=tk.LEFT, padx=4)
            ttk.Button(f_b, text="📷 Escanear Cripto",
                       command=lambda: [popup.destroy(),
                                        self.escanear_cripto_pipeline()]).pack(side=tk.LEFT, padx=4)
            ttk.Button(f_b, text="❌ Cerrar",
                       command=popup.destroy).pack(side=tk.RIGHT, padx=4)

    def _cerrar_panel_foto(self):
        """Cierra el panel lateral de foto dentro de la ventana HD."""
        if self.panel_foto_hd and self.panel_foto_hd.winfo_exists():
            self.panel_foto_hd.destroy()
            self.panel_foto_hd = None

    def _foto_hd(self):
        """Captura foto. Si stream activo → usa frame en RAM (sin HTTP). Muestra en panel HD."""
        def _run():
            img = None
            if self.stream_activo and self.ultimo_frame_cv2 is not None:
                # ✅ Clave Opción 1+2: frame ya en RAM, cero peticiones HTTP
                img = self.ultimo_frame_cv2.copy()
                self.agregar_log_consola(
                    "[CÁMARA HD] ✓ Foto tomada del frame en RAM (sin interrumpir stream)")
            else:
                _, capture_url, _ = self._get_cam_urls()
                self.agregar_log_consola(f"[CÁMARA HD] Capturando foto desde {capture_url}...")
                t0 = time.time()
                try:
                    r = requests.get(capture_url, timeout=6)
                    t_trans = (time.time() - t0) * 1000
                    if r.status_code == 200:
                        arr = np.frombuffer(r.content, np.uint8)
                        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                        if img is not None:
                            h, w, _ = img.shape
                            self.agregar_log_consola(
                                f"[CÁMARA HD] ✓ Foto capturada: {w}x{h} px, "
                                f"{len(r.content)/1024:.1f} KB, {t_trans:.0f} ms")
                    else:
                        self.agregar_log_consola(f"[CÁMARA HD] ✗ HTTP {r.status_code}")
                except Exception as e:
                    self.agregar_log_consola(f"[CÁMARA HD] ✗ Error: {e}")

            if img is not None:
                self.ultimo_frame_cv2 = img
                self.root.after(0, lambda i=img: self._mostrar_foto_panel(i))

        threading.Thread(target=_run, daemon=True).start()


    def _guardar_foto_png(self, img_bgr):
        """Guarda la foto capturada como PNG en la carpeta fotos_capturadas."""
        import os
        carpeta = os.path.join(os.path.dirname(__file__), "..", "fotos_capturadas")
        os.makedirs(carpeta, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        ruta = os.path.join(carpeta, f"foto_{ts}.png")
        cv2.imwrite(ruta, img_bgr)
        self.agregar_log_consola(f"[FOTO] ✓ Guardada en: {ruta}")


    def _renderizar_frame_hd(self, frame_bgr):
        """Renderiza frame OpenCV en el canvas_agrandar (hilo GUI)."""
        if self.canvas_agrandar is None:
            return
        try:
            cw = self.canvas_agrandar.winfo_width()
            ch = self.canvas_agrandar.winfo_height()
            if cw < 10 or ch < 10:
                cw, ch = 960, 620
            img_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            img_hd = Image.fromarray(img_rgb).resize((cw, ch), Image.Resampling.LANCZOS)
            self.cam_hd_tk = ImageTk.PhotoImage(img_hd)
            self.canvas_agrandar.delete("all")
            self.canvas_agrandar.create_image(0, 0, image=self.cam_hd_tk, anchor='nw')
        except Exception:
            pass

    def _bucle_hd_canvas(self):
        """Bucle dedicado que mantiene el canvas HD actualizado mientras stream_activo."""
        while self.stream_activo:
            if self.window_agrandar and self.window_agrandar.winfo_exists() and self.ultimo_frame_cv2 is not None:
                frame = self.ultimo_frame_cv2.copy()
                self.root.after(0, lambda f=frame: self._renderizar_frame_hd(f))
            time.sleep(0.04)  # ~25 FPS en la ventana HD

    def _bucle_video_stream(self):
        stream_url, capture_url, _ = self._get_cam_urls()
        session = requests.Session()
        frames_count = 0
        t_start_fps = time.time()

        # ── Modo 1: MJPEG Stream Continuo ────────────────────────────────────────
        try:
            r_stream = session.get(stream_url, stream=True, timeout=5)
            if r_stream.status_code == 200:
                self.agregar_log_consola(f"[CÁMARA] ✓ Conectado al stream MJPEG: {stream_url}")
                bytes_buf = b""
                for chunk in r_stream.iter_content(chunk_size=4096):
                    if not self.stream_activo:
                        break
                    bytes_buf += chunk
                    a = bytes_buf.find(b'\xff\xd8')
                    b = bytes_buf.find(b'\xff\xd9')
                    if a != -1 and b != -1:
                        jpg = bytes_buf[a:b+2]
                        bytes_buf = bytes_buf[b+2:]
                        img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                        if img is not None:
                            self.ultimo_frame_cv2 = img
                            h, w, _ = img.shape
                            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                            img_pil = Image.fromarray(img_rgb).resize((400, 266), Image.Resampling.LANCZOS)
                            self.cam_img_tk = ImageTk.PhotoImage(img_pil)

                            frames_count += 1
                            elapsed_fps = time.time() - t_start_fps
                            fps = frames_count / elapsed_fps if elapsed_fps > 0 else 0

                            def _update_stream_gui(fps_val=fps, width=w, height=h, size=len(jpg)/1024.0):
                                self.canvas_cam.delete("all")
                                self.canvas_cam.create_image(0, 0, image=self.cam_img_tk, anchor='nw')
                                self.lbl_metrics_cam.configure(text=f"Res: {width}x{height} px | Size: {size:.1f} KB | FPS: {fps_val:.1f}")
                                self.lbl_status_cam.configure(text=f"Estado: 🟢 STREAMING ({fps_val:.1f} FPS)", foreground=CLR_GREEN)
                                self.lbl_ind_cam.configure(text=f"🟢 ESP32-CAM ({fps_val:.1f} FPS)", foreground=CLR_GREEN)

                            self.root.after(0, _update_stream_gui)
                session.close()
                return
        except Exception:
            pass

        # Fallback a consulta ultrarrápida /capture con sesión HTTP persistente
        while self.stream_activo:
            t0 = time.time()
            try:
                r = session.get(capture_url, timeout=2)
                t_trans = (time.time() - t0) * 1000
                if r.status_code == 200:
                    size_kb = len(r.content) / 1024.0
                    arr = np.frombuffer(r.content, np.uint8)
                    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                    if img is not None:
                        self.ultimo_frame_cv2 = img
                        h, w, _ = img.shape
                        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        img_pil = Image.fromarray(img_rgb).resize((400, 266), Image.Resampling.LANCZOS)
                        self.cam_img_tk = ImageTk.PhotoImage(img_pil)

                        frames_count += 1
                        elapsed_fps = time.time() - t_start_fps
                        fps = frames_count / elapsed_fps if elapsed_fps > 0 else 0

                        def _update_gui(fps_val=fps, lat=t_trans, width=w, height=h, size=size_kb):
                            self.canvas_cam.delete("all")
                            self.canvas_cam.create_image(0, 0, image=self.cam_img_tk, anchor='nw')
                            self.lbl_metrics_cam.configure(text=f"Res: {width}x{height} px | Size: {size:.1f} KB | Latencia: {lat:.0f} ms | FPS: {fps_val:.1f}")
                            self.lbl_status_cam.configure(text=f"Estado: 🟢 STREAMING ({fps_val:.1f} FPS)", foreground=CLR_GREEN)
                            self.lbl_ind_cam.configure(text=f"🟢 ESP32-CAM ({fps_val:.1f} FPS)", foreground=CLR_GREEN)

                        self.root.after(0, _update_gui)
                time.sleep(0.01)
            except Exception as e:
                self.agregar_log_consola(f"[STREAM ERR] {e}")
                time.sleep(0.5)

        session.close()
        def _reset_gui():
            self.lbl_status_cam.configure(text="Estado: ⚪ IDLE", foreground=TEXT_MUTED)
        self.root.after(0, _reset_gui)

    def escanear_cripto_pipeline(self):
        def _run():

            self.agregar_log_consola("[PIPELINE IA] Iniciando escaneo de criptomoneda...")
            esp32_comm.enviar_comando_oled("PROCESANDO")

            # Obtener frame: de RAM (stream activo) o petición HTTP
            frame = None
            if getattr(self, 'ultimo_frame_cv2', None) is not None and self.stream_activo:
                frame = self.ultimo_frame_cv2.copy()
                self.agregar_log_consola("[PIPELINE IA] Usando frame en RAM (stream activo)...")
            else:
                _, capture_url, _ = self._get_cam_urls()
                self.agregar_log_consola(f"[PIPELINE IA] Capturando fotograma desde {capture_url}...")
                try:
                    r = requests.get(capture_url, timeout=6)
                    if r.status_code == 200:
                        arr = np.frombuffer(r.content, np.uint8)
                        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                except Exception as e:
                    self.agregar_log_consola(f"[PIPELINE ERROR] {e}")

            if frame is None:
                esp32_comm.enviar_comando_oled("ERROR")
                self.agregar_log_consola("[PIPELINE ERROR] No se pudo obtener fotograma de la cámara.")
                return

            # Detectar con el sistema unificado (Gemini → ORB)
            detector = DetectorCriptoUnificado()
            cripto, conf, modo = detector.detectar(frame)

            modo_icon = "🧠 Gemini AI" if modo == "gemini" else "🔍 ORB local"
            conf_pct = conf * 100.0

            if cripto:
                activo_lower = cripto.lower()
                # Mapear al nombre mostrable
                from config import CRYPTO_MAP
                info = CRYPTO_MAP.get(activo_lower, {})
                symbol = info.get("symbol", activo_lower.upper())
                nombre_display = activo_lower.upper()

                self.agregar_log_consola(
                    f"[PIPELINE IA] ✅ Activo: '{nombre_display}' ({symbol}) | "
                    f"Confianza: {conf_pct:.1f}% | Modo: {modo_icon}")

                # Anotar recuadro verde en el frame
                img_ann = frame.copy()
                h, w, _ = img_ann.shape
                color_ann = (0, 210, 135)
                cv2.rectangle(img_ann, (15, 15), (w-15, h-15), color_ann, 3)
                cv2.putText(img_ann, f"{nombre_display} ({conf_pct:.0f}%) [{modo_icon}]",
                            (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color_ann, 2)

                img_rgb = cv2.cvtColor(img_ann, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(img_rgb).resize((400, 266), Image.Resampling.LANCZOS)
                self.cam_img_tk = ImageTk.PhotoImage(img_pil)
                self.root.after(0, lambda: self.canvas_cam.delete("all") or
                                self.canvas_cam.create_image(0, 0, image=self.cam_img_tk, anchor='nw'))

                # Obtener datos de mercado
                resp, _ = generar_respuesta_precio(symbol)
                self.agregar_log_consola(f"[PIPELINE API] {resp.splitlines()[0] if resp else 'Sin datos de API'}")

                esp32_comm.enviar_comando_oled("RESPONDIENDO")

                def _update_ui():
                    self.notebook.select(self.tab_mercado)
                    self.entry_ticker.delete(0, tk.END)
                    self.entry_ticker.insert(0, symbol)
                    self.txt_mercado.configure(state='normal')
                    self.txt_mercado.delete("1.0", tk.END)
                    self.txt_mercado.insert(
                        tk.END,
                        f"{resp}\n\n"
                        f"🧠 Detección: {modo_icon} | Confianza: {conf_pct:.1f}%\n"
                        f"💡 Usa '🎤 Hablar sobre este Activo' para preguntar por voz sobre "
                        f"historial, precio o creadores."
                    )
                    self.txt_mercado.configure(state='disabled')
                    self.agregar_mensaje(
                        "Asistente Experto",
                        f"🔍 [Análisis Visual IA — {modo_icon}]: **{nombre_display}** detectado "
                        f"con {conf_pct:.1f}% de confianza.\n\n{resp}",
                        "bot"
                    )

                self.root.after(0, _update_ui)
                hablar(f"Criptomoneda identificada: {nombre_display}. {resp.splitlines()[0] if resp else ''}")
                esp32_comm.enviar_comando_oled("IDLE")

            else:
                esp32_comm.enviar_comando_oled("ERROR")
                msg = (
                    "No se reconoció un logotipo con suficiente certeza.\n"
                    "Consejos:\n"
                    "  • Centra el logo en la cámara (al menos 30% del encuadre)\n"
                    "  • Evita reflejos o fondo muy oscuro\n"
                    "  • Criptos soportadas: Bitcoin, Ethereum, Cardano, Solana, XRP, Dogecoin, BNB"
                )
                self.agregar_log_consola(f"[PIPELINE IA] ⚠️ No reconocido (modo: {modo_icon})")
                self.agregar_mensaje("Asistente Experto", f"⚠️ {msg}", "bot")
                hablar("No se reconoció la criptomoneda. Centra el logotipo ante la cámara.")

        threading.Thread(target=_run, daemon=True).start()


    # --------------------------------------------------------------------------
    # TAB 2: CHAT CONVERSACIONAL (ESTILO CHATGPT)
    # --------------------------------------------------------------------------
    def configurar_tab_chat(self):
        container = ttk.Frame(self.tab_chat, style="Card.TFrame")
        container.pack(expand=True, fill='both', padx=10, pady=10)

        # Catálogo de Preguntas Sugeridas
        f_cat = ttk.Frame(container, style="Card.TFrame")
        f_cat.pack(side=tk.BOTTOM, fill='x', padx=15, pady=(0, 5))

        f_cat_top = ttk.Frame(f_cat, style="Card.TFrame")
        f_cat_top.pack(fill='x', padx=5, pady=(4, 2))

        ttk.Label(f_cat_top, text="💡 CATÁLOGO DE PREGUNTAS Y COMANDOS SUGERIDOS:", font=("Segoe UI", 11, "bold"), foreground=CLR_GREEN).pack(side=tk.LEFT)
        ttk.Button(f_cat_top, text="📖 Desplegar Todo el Conocimiento", command=self.desplegar_catalogo_completo).pack(side=tk.RIGHT)

        f_chips = ttk.Frame(f_cat, style="Card.TFrame")
        f_chips.pack(fill='x', padx=5, pady=4)

        preguntas_sugeridas = [
            "¿Qué es la inflación?",
            "¿Cómo ahorrar dinero?",
            "¿Qué es Bitcoin?",
            "¿Qué es el interés compuesto?",
            "¿Cómo reducir riesgo?",
            "¿Qué es un ETF?",
            "¿Qué es un mercado alcista?",
            "Precio de BTC"
        ]

        for p in preguntas_sugeridas:
            b = tk.Button(
                f_chips, text=p, font=("Segoe UI", 10, "bold"), bg=BG_ENTRY, fg=CLR_CYAN,
                activebackground=CLR_GREEN, activeforeground="#000000", bd=1, relief="solid", padx=10, pady=6,
                cursor="hand2", command=lambda txt=p: self._ejecutar_pregunta_catalogo(txt)
            )
            b.pack(side=tk.LEFT, padx=4, pady=3)

        # Entrada de Texto y Voz abajo
        f_input = ttk.Frame(container, style="Card.TFrame")
        f_input.pack(side=tk.BOTTOM, fill='x', padx=15, pady=10)

        btn_detener = ttk.Button(f_input, text="🛑 Detener Voz", command=detener_habla)
        btn_detener.pack(side=tk.RIGHT, padx=4)

        btn_voz = ttk.Button(f_input, text="🎙️ Hablar (INMP441)", command=self.consultar_voz_mic_fisico)
        btn_voz.pack(side=tk.RIGHT, padx=4)

        btn_enviar = ttk.Button(f_input, text="➤ Enviar", command=self.consultar_texto)
        btn_enviar.pack(side=tk.RIGHT, padx=4)

        self.entry_consulta = tk.Entry(f_input, font=("Segoe UI", 12), bg=BG_ENTRY, fg=TEXT_MAIN, insertbackground=TEXT_MAIN)
        self.entry_consulta.pack(side=tk.LEFT, expand=True, fill='x', ipady=8, padx=(0, 10))
        self.entry_consulta.bind("<Return>", lambda e: self.consultar_texto())

        # Historial Chat Conversacional
        self.historial = scrolledtext.ScrolledText(container, state='disabled', wrap=tk.WORD, font=("Segoe UI", 11), bg=BG_MAIN, fg=TEXT_MAIN, borderwidth=0)
        self.historial.pack(side=tk.TOP, expand=True, fill='both', padx=10, pady=10)

        self.historial.tag_config('user', foreground=CLR_GREEN, font=("Segoe UI", 12, "bold"))
        self.historial.tag_config('bot', foreground=TEXT_MAIN)

        self.agregar_mensaje("Asistente Experto", "¡Hola! Soy tu asistente financiero en tiempo real. Puedes seleccionar cualquier pregunta del catálogo o hablar a través del micrófono INMP441.\n", "bot")

    def _ejecutar_pregunta_catalogo(self, texto):
        self.entry_consulta.delete(0, tk.END)
        self.entry_consulta.insert(0, texto)
        self.consultar_texto()

    def desplegar_catalogo_completo(self):
        """Muestra una ventana modal interactiva maximizada y totalmente acoplada al tamaño de cualquier pantalla."""
        win_cat = tk.Toplevel(self.root)
        win_cat.title("📖 Catálogo Completo de Conocimiento Financiero")
        
        # Ajustar dinámicamente al 85% de la pantalla actual o pantalla completa
        w = max(900, int(self.root.winfo_width() * 0.90))
        h = max(650, int(self.root.winfo_height() * 0.85))
        win_cat.geometry(f"{w}x{h}")
        win_cat.configure(bg=BG_MAIN)

        ttk.Label(win_cat, text="📖 CATÁLOGO COMPLETO DE CONOCIMIENTO FINANCIERO", font=FONT_TITLE, foreground=CLR_GREEN).pack(pady=12)
        ttk.Label(win_cat, text="Selecciona cualquiera de las preguntas o comandos de la lista para consultarlo de inmediato:", font=FONT_BODY, foreground=TEXT_MUTED).pack(pady=(0, 8))

        f_scroll = ttk.Frame(win_cat, style="Card.TFrame")
        f_scroll.pack(expand=True, fill='both', padx=15, pady=10)

        canvas = tk.Canvas(f_scroll, bg=BG_ENTRY, highlightthickness=0)
        scrollbar = ttk.Scrollbar(f_scroll, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="Card.TFrame")

        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_frame_id, width=event.width)

        canvas_frame_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.bind("<Configure>", _on_canvas_configure)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

        try:
            from conocimiento.database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT nombre, definicion FROM conceptos")
            conceptos = [dict(row) for row in cursor.fetchall()]
            cursor.execute("SELECT condicion, conclusion FROM reglas")
            reglas = [dict(row) for row in cursor.fetchall()]
            conn.close()

            ttk.Label(scrollable_frame, text="💡 CONCEPTOS FINANCIEROS DISPONIBLES", font=("Segoe UI", 12, "bold"), foreground=CLR_CYAN).pack(anchor='w', padx=10, pady=(10, 5))

            f_grid1 = ttk.Frame(scrollable_frame, style="Card.TFrame")
            f_grid1.pack(fill='x', expand=True, padx=10, pady=5)
            for col_i in range(4):
                f_grid1.grid_columnconfigure(col_i, weight=1)

            col = 0
            row = 0
            for c in conceptos:
                nombre = c.get('nombre', '')
                q_text = f"¿Qué es {nombre.lower()}?"
                b = tk.Button(
                    f_grid1, text=q_text, font=("Segoe UI", 10, "bold"), bg="#1A2332", fg=CLR_GREEN,
                    activebackground=CLR_GREEN, activeforeground="#000000", bd=1, relief="solid", padx=10, pady=8,
                    cursor="hand2", command=lambda txt=q_text, w=win_cat: [w.destroy(), self._ejecutar_pregunta_catalogo(txt)]
                )
                b.grid(row=row, column=col, padx=4, pady=4, sticky="ew")
                col += 1
                if col >= 4:
                    col = 0
                    row += 1

            ttk.Label(scrollable_frame, text="⚙️ ESTRATEGIAS Y REGLAS DE DECISIÓN", font=("Segoe UI", 12, "bold"), foreground=CLR_CYAN).pack(anchor='w', padx=10, pady=(15, 5))

            f_grid2 = ttk.Frame(scrollable_frame, style="Card.TFrame")
            f_grid2.pack(fill='x', expand=True, padx=10, pady=5)
            for col_i in range(4):
                f_grid2.grid_columnconfigure(col_i, weight=1)

            col = 0
            row = 0
            for r in reglas:
                cond = r.get('condicion', '')
                q_text = cond.capitalize()
                b = tk.Button(
                    f_grid2, text=q_text, font=("Segoe UI", 10, "bold"), bg="#1A2332", fg=CLR_CYAN,
                    activebackground=CLR_GREEN, activeforeground="#000000", bd=1, relief="solid", padx=10, pady=8,
                    cursor="hand2", command=lambda txt=q_text, w=win_cat: [w.destroy(), self._ejecutar_pregunta_catalogo(txt)]
                )
                b.grid(row=row, column=col, padx=4, pady=4, sticky="ew")
                col += 1
                if col >= 4:
                    col = 0
                    row += 1

            ttk.Label(scrollable_frame, text="📈 MERCADOS CRIPTO EN TIEMPO REAL Y VISIÓN IA", font=("Segoe UI", 12, "bold"), foreground=CLR_CYAN).pack(anchor='w', padx=10, pady=(15, 5))

            f_grid3 = ttk.Frame(scrollable_frame, style="Card.TFrame")
            f_grid3.pack(fill='x', expand=True, padx=10, pady=5)
            for col_i in range(4):
                f_grid3.grid_columnconfigure(col_i, weight=1)

            comandos_cripto = ["Precio de BTC", "Precio de ETH", "Precio de SOL", "Escanear Cripto"]
            for idx, c in enumerate(comandos_cripto):
                b = tk.Button(
                    f_grid3, text=c, font=("Segoe UI", 10, "bold"), bg="#1A2332", fg="#FFD700",
                    activebackground=CLR_GREEN, activeforeground="#000000", bd=1, relief="solid", padx=10, pady=8,
                    cursor="hand2", command=lambda txt=c, w=win_cat: [w.destroy(), self._ejecutar_pregunta_catalogo(txt)]
                )
                b.grid(row=0, column=idx, padx=4, pady=4, sticky="ew")

        except Exception as ex:
            ttk.Label(scrollable_frame, text=f"Error cargando catálogo: {ex}", foreground=CLR_RED).pack(padx=10, pady=10)

    def consultar_voz_mic_fisico(self):
        def _run():
            self.agregar_mensaje("Usuario", "🎙️ [🔴 ESCUCHANDO — Habla ahora al micrófono INMP441 por 4 segundos...]", "user")
            esp32_comm.enviar_comando_oled("ESCUCHANDO")
            metrics, res = esp32_comm.capturar_audio_mic(4)
            esp32_comm.enviar_comando_oled("PROCESANDO")
            
            if metrics and "pcm_bytes" in metrics:
                dur = metrics.get("duracion", 4.0)
                rms = metrics.get("rms", 0.0)
                self.agregar_log_consola(f"[MIC AUDIO VERIFICADO] Captura recibida: {dur:.1f}s | Nivel RMS={rms:.1f}")
                
                texto = escuchar_desde_pcm(metrics["pcm_bytes"])
                self.agregar_mensaje("Usuario", f"🎙️ \"{texto}\"", "user")
                resp, _ = procesar_consulta(texto)
                self.agregar_mensaje("Asistente Experto", resp, "bot")
                esp32_comm.enviar_comando_oled("RESPONDIENDO")
                hablar(resp)
                esp32_comm.enviar_comando_oled("IDLE")
            else:
                self.agregar_mensaje("Asistente Experto", "No se recibió audio del micrófono INMP441. Verifica el cableado I2S en COM5.", "bot")
                esp32_comm.enviar_comando_oled("ERROR")

        threading.Thread(target=_run, daemon=True).start()

    def consultar_texto(self):
        txt = self.entry_consulta.get().strip()
        if not txt: return
        self.entry_consulta.delete(0, tk.END)
        self.agregar_mensaje("Usuario", txt, "user")
        def _run():
            resp, _ = procesar_consulta(txt)
            self.agregar_mensaje("Asistente Experto", resp, "bot")
            hablar(resp)
        threading.Thread(target=_run, daemon=True).start()

    def agregar_mensaje(self, emisor, texto, tag):
        def _append():
            self.historial.configure(state='normal')
            self.historial.insert(tk.END, f"{emisor}: ", tag)
            self.historial.insert(tk.END, f"{texto}\n\n")
            self.historial.see(tk.END)
            self.historial.configure(state='disabled')
        self.root.after(0, _append)

    # --------------------------------------------------------------------------
    # TAB 3: MERCADO EN TIEMPO REAL
    # --------------------------------------------------------------------------
    def configurar_tab_mercado(self):
        container = ttk.Frame(self.tab_mercado, style="Card.TFrame")
        container.pack(expand=True, fill='both', padx=15, pady=15)

        ttk.Label(container, text="📈 MERCADO EN TIEMPO REAL (ACCIONES Y CRIPTO)", font=FONT_SUB, foreground=CLR_GREEN).pack(anchor='w', pady=(0, 10))

        f_in = ttk.Frame(container, style="Card.TFrame")
        f_in.pack(fill='x', pady=8)

        ttk.Label(f_in, text="Ticker (ej. AAPL, TSLA, BTC, ETH): ", font=FONT_BODY).pack(side=tk.LEFT, padx=5)
        self.entry_ticker = tk.Entry(f_in, font=FONT_BODY, bg=BG_ENTRY, fg=TEXT_MAIN, width=15)
        self.entry_ticker.pack(side=tk.LEFT, padx=5)

        ttk.Button(f_in, text="📊 Consultar Mercado", command=self.consultar_mercado).pack(side=tk.LEFT, padx=5)
        ttk.Button(f_in, text="🎙️ Hablar sobre este Activo (INMP441)", command=self.consultar_voz_mercado).pack(side=tk.LEFT, padx=5)

        self.txt_mercado = scrolledtext.ScrolledText(container, state='disabled', wrap=tk.WORD, font=("Segoe UI", 12), bg=BG_ENTRY, fg=TEXT_MAIN, height=12)
        self.txt_mercado.pack(expand=True, fill='both', pady=10)

    def consultar_mercado(self):
        ticker = self.entry_ticker.get().strip()
        if not ticker: return
        def _run():
            resp, logs = generar_respuesta_precio(ticker)
            def _update():
                self.txt_mercado.configure(state='normal')
                self.txt_mercado.delete("1.0", tk.END)
                self.txt_mercado.insert(tk.END, resp)
                self.txt_mercado.configure(state='disabled')
            self.root.after(0, _update)
        threading.Thread(target=_run, daemon=True).start()

    def consultar_voz_mercado(self):
        ticker_actual = self.entry_ticker.get().strip() or "BTC"
        def _run():
            def _prep():
                self.txt_mercado.configure(state='normal')
                self.txt_mercado.delete("1.0", tk.END)
                self.txt_mercado.insert(tk.END, f"🎙️ [🔴 ESCUCHANDO — Pregunta algo sobre {ticker_actual.upper()} por el micrófono INMP441 por 4 segundos...]\n")
                self.txt_mercado.configure(state='disabled')
            self.root.after(0, _prep)
            
            esp32_comm.enviar_comando_oled("ESCUCHANDO")
            metrics, res = esp32_comm.capturar_audio_mic(4)
            esp32_comm.enviar_comando_oled("PROCESANDO")
            
            if metrics and "pcm_bytes" in metrics:
                pregunta = escuchar_desde_pcm(metrics["pcm_bytes"])
                consulta_combinada = f"{pregunta} {ticker_actual}"
                resp, _ = procesar_consulta(consulta_combinada)
                
                def _update():
                    self.txt_mercado.configure(state='normal')
                    self.txt_mercado.delete("1.0", tk.END)
                    self.txt_mercado.insert(tk.END, f"🎙️ Pregunta por Voz: \"{pregunta}\"\n\n🤖 RESPUESTA DEL ASISTENTE EXPERTO:\n{resp}\n")
                    self.txt_mercado.configure(state='disabled')
                    
                self.root.after(0, _update)
                esp32_comm.enviar_comando_oled("RESPONDIENDO")
                hablar(resp)
                esp32_comm.enviar_comando_oled("IDLE")
            else:
                def _err():
                    self.txt_mercado.configure(state='normal')
                    self.txt_mercado.insert(tk.END, "\n❌ No se recibió audio del micrófono INMP441.")
                    self.txt_mercado.configure(state='disabled')
                self.root.after(0, _err)
                esp32_comm.enviar_comando_oled("ERROR")

        threading.Thread(target=_run, daemon=True).start()

    # --------------------------------------------------------------------------
    # TAB 4: ENTRENAMIENTO BASE
    # --------------------------------------------------------------------------
    def configurar_tab_entrenamiento(self):
        container = ttk.Frame(self.tab_entrenamiento, style="Card.TFrame")
        container.pack(expand=True, fill='both', padx=15, pady=15)

        sub_nb = ttk.Notebook(container)
        sub_nb.pack(expand=True, fill='both', padx=5, pady=5)

        # Conceptos
        f_c = ttk.Frame(sub_nb, style="Card.TFrame")
        sub_nb.add(f_c, text="💡 Conceptos")
        ttk.Label(f_c, text="Nombre del Concepto:").pack(anchor='w', padx=15, pady=(15, 2))
        self.ent_conc_nombre = tk.Entry(f_c, font=FONT_BODY, bg=BG_ENTRY, fg=TEXT_MAIN)
        self.ent_conc_nombre.pack(fill='x', padx=15, pady=5)
        ttk.Label(f_c, text="Definición:").pack(anchor='w', padx=15, pady=(10, 2))
        self.ent_conc_def = tk.Entry(f_c, font=FONT_BODY, bg=BG_ENTRY, fg=TEXT_MAIN)
        self.ent_conc_def.pack(fill='x', padx=15, pady=5)
        ttk.Button(f_c, text="💾 Guardar Concepto", command=self.agregar_concepto_gui).pack(anchor='e', padx=15, pady=15)

        # Relaciones
        f_r = ttk.Frame(sub_nb, style="Card.TFrame")
        sub_nb.add(f_r, text="🔗 Relaciones")
        ttk.Label(f_r, text="Origen:").pack(anchor='w', padx=15, pady=(15, 2))
        self.ent_rel_orig = tk.Entry(f_r, font=FONT_BODY, bg=BG_ENTRY, fg=TEXT_MAIN)
        self.ent_rel_orig.pack(fill='x', padx=15, pady=5)
        ttk.Label(f_r, text="Relación:").pack(anchor='w', padx=15, pady=(5, 2))
        self.ent_rel_tipo = tk.Entry(f_r, font=FONT_BODY, bg=BG_ENTRY, fg=TEXT_MAIN)
        self.ent_rel_tipo.pack(fill='x', padx=15, pady=5)
        ttk.Label(f_r, text="Destino:").pack(anchor='w', padx=15, pady=(5, 2))
        self.ent_rel_dest = tk.Entry(f_r, font=FONT_BODY, bg=BG_ENTRY, fg=TEXT_MAIN)
        self.ent_rel_dest.pack(fill='x', padx=15, pady=5)
        ttk.Button(f_r, text="💾 Guardar Relación", command=self.agregar_relacion_gui).pack(anchor='e', padx=15, pady=15)

        # Reglas
        f_reg = ttk.Frame(sub_nb, style="Card.TFrame")
        sub_nb.add(f_reg, text="⚡ Reglas")
        ttk.Label(f_reg, text="Condición:").pack(anchor='w', padx=15, pady=(15, 2))
        self.ent_reg_cond = tk.Entry(f_reg, font=FONT_BODY, bg=BG_ENTRY, fg=TEXT_MAIN)
        self.ent_reg_cond.pack(fill='x', padx=15, pady=5)
        ttk.Label(f_reg, text="Conclusión:").pack(anchor='w', padx=15, pady=(5, 2))
        self.ent_reg_conc = tk.Entry(f_reg, font=FONT_BODY, bg=BG_ENTRY, fg=TEXT_MAIN)
        self.ent_reg_conc.pack(fill='x', padx=15, pady=5)
        ttk.Button(f_reg, text="💾 Guardar Regla", command=self.agregar_regla_gui).pack(anchor='e', padx=15, pady=15)

    def agregar_concepto_gui(self):
        n = self.ent_conc_nombre.get().strip()
        d = self.ent_conc_def.get().strip()
        if n and d:
            msg = nuevo_concepto(n, d)
            messagebox.showinfo("Entrenamiento", msg)
            self.ent_conc_nombre.delete(0, tk.END)
            self.ent_conc_def.delete(0, tk.END)

    def agregar_relacion_gui(self):
        o = self.ent_rel_orig.get().strip()
        r = self.ent_rel_tipo.get().strip()
        dest = self.ent_rel_dest.get().strip()
        if o and r and dest:
            msg = nueva_relacion(o, r, dest)
            messagebox.showinfo("Entrenamiento", msg)
            self.ent_rel_orig.delete(0, tk.END)
            self.ent_rel_tipo.delete(0, tk.END)
            self.ent_rel_dest.delete(0, tk.END)

    def agregar_regla_gui(self):
        c = self.ent_reg_cond.get().strip()
        conc = self.ent_reg_conc.get().strip()
        if c and conc:
            msg = nueva_regla(c, conc)
            messagebox.showinfo("Entrenamiento", msg)
            self.ent_reg_cond.delete(0, tk.END)
            self.ent_reg_conc.delete(0, tk.END)

    # --------------------------------------------------------------------------
    # TAB 5: BASE DE CONOCIMIENTO
    # --------------------------------------------------------------------------
    def _on_tab_change(self, event):
        selected = self.notebook.index(self.notebook.select())
        if selected == 4:
            self.recargar_conocimiento()

    def configurar_tab_conocimiento(self):
        container = ttk.Frame(self.tab_conocimiento, style="Card.TFrame")
        container.pack(expand=True, fill='both', padx=10, pady=10)

        f_top = ttk.Frame(container, style="Card.TFrame")
        f_top.pack(fill='x', padx=15, pady=5)
        ttk.Label(f_top, text="📚 BASE DE CONOCIMIENTO SQLITE", font=FONT_SUB, foreground=CLR_GREEN).pack(side=tk.LEFT)
        ttk.Button(f_top, text="🔄 Actualizar BD", command=self.recargar_conocimiento).pack(side=tk.RIGHT)

        sub_nb = ttk.Notebook(container)
        sub_nb.pack(expand=True, fill='both', padx=10, pady=5)

        f_conc = ttk.Frame(sub_nb, style="TFrame")
        sub_nb.add(f_conc, text="💡 Conceptos")
        self.tree_conceptos = ttk.Treeview(f_conc, columns=("#", "Nombre", "Definición"), show='headings')
        self._configurar_treeview(self.tree_conceptos, [("#", 40), ("Nombre", 160), ("Definición", 600)])
        self.tree_conceptos.pack(expand=True, fill='both', padx=5, pady=5)

        f_rel = ttk.Frame(sub_nb, style="TFrame")
        sub_nb.add(f_rel, text="🔗 Relaciones")
        self.tree_relaciones = ttk.Treeview(f_rel, columns=("#", "Origen", "Relación", "Destino"), show='headings')
        self._configurar_treeview(self.tree_relaciones, [("#", 40), ("Origen", 160), ("Relación", 200), ("Destino", 160)])
        self.tree_relaciones.pack(expand=True, fill='both', padx=5, pady=5)

        f_reg = ttk.Frame(sub_nb, style="TFrame")
        sub_nb.add(f_reg, text="⚡ Reglas")
        self.tree_reglas = ttk.Treeview(f_reg, columns=("#", "Condición", "Conclusión"), show='headings')
        self._configurar_treeview(self.tree_reglas, [("#", 40), ("Condición", 250), ("Conclusión", 500)])
        self.tree_reglas.pack(expand=True, fill='both', padx=5, pady=5)

        self.recargar_conocimiento()

    def _configurar_treeview(self, tree, columnas):
        style_name = f"{id(tree)}.Treeview"
        s = ttk.Style()
        s.configure(style_name, background=BG_ENTRY, foreground=TEXT_MAIN, fieldbackground=BG_ENTRY, rowheight=28, font=FONT_BODY)
        s.configure(f"{style_name}.Heading", background=BG_CARD, foreground=CLR_GREEN, font=("Segoe UI", 10, "bold"))
        tree.configure(style=style_name)

        for col, width in columnas:
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor='w' if col != "#" else 'center')

        sb = ttk.Scrollbar(tree.master, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    def recargar_conocimiento(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id, nombre, definicion FROM conceptos ORDER BY nombre")
            conceptos = cursor.fetchall()
            self.tree_conceptos.delete(*self.tree_conceptos.get_children())
            for i, row in enumerate(conceptos, 1):
                self.tree_conceptos.insert('', 'end', values=(i, row['nombre'].capitalize(), row['definicion']))

            cursor.execute("SELECT id, origen, tipo_relacion, destino FROM relaciones ORDER BY origen")
            relaciones = cursor.fetchall()
            self.tree_relaciones.delete(*self.tree_relaciones.get_children())
            for i, row in enumerate(relaciones, 1):
                self.tree_relaciones.insert('', 'end', values=(i, row['origen'], row['tipo_relacion'], row['destino']))

            cursor.execute("SELECT id, condicion, conclusion FROM reglas ORDER BY id")
            reglas = cursor.fetchall()
            self.tree_reglas.delete(*self.tree_reglas.get_children())
            for i, row in enumerate(reglas, 1):
                self.tree_reglas.insert('', 'end', values=(i, row['condicion'], row['conclusion']))

            conn.close()
        except Exception:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = AsistenteApp(root)
    root.mainloop()
