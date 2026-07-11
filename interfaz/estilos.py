"""
Constantes de estilo y configuración del tema visual.
Extraído de app.py para reutilización en todos los paneles.
"""
from tkinter import ttk

# --- Colores del Tema Oscuro Premium ---
BG_COLOR = "#121212"
CARD_COLOR = "#1E1E1E"
TEXT_COLOR = "#FFFFFF"
MUTED_TEXT = "#B3B3B3"
ACCENT_COLOR = "#00D287"    # Verde financiero
ACCENT_HOVER = "#00A96B"
ERROR_COLOR = "#FF4C4C"     # Rojo para errores/caídas
WARNING_COLOR = "#FFB347"   # Naranja para advertencias
SUCCESS_COLOR = "#00D287"   # Verde para éxito/subidas
INPUT_BG = "#2A2A2A"

# --- Fuentes ---
FONT_MAIN = ("Segoe UI", 12)
FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_SUBTITLE = ("Segoe UI", 13, "bold")
FONT_CODE = ("Consolas", 11)
FONT_SMALL = ("Segoe UI", 10)
FONT_PRICE = ("Segoe UI", 20, "bold")

def configurar_estilos(style=None):
    """
    Configura todos los estilos ttk del tema oscuro.
    Si no se pasa un estilo, crea uno nuevo.
    """
    if style is None:
        style = ttk.Style()
    
    style.theme_use('clam')
    
    # Notebook (Pestañas)
    style.configure("TNotebook", background=BG_COLOR, borderwidth=0)
    style.configure("TNotebook.Tab", background=CARD_COLOR, foreground=TEXT_COLOR, 
                     padding=[20, 10], font=FONT_MAIN, borderwidth=0)
    style.map("TNotebook.Tab", 
               background=[("selected", ACCENT_COLOR)], 
               foreground=[("selected", "#000000")])
    
    # Frames
    style.configure("TFrame", background=BG_COLOR)
    style.configure("Card.TFrame", background=CARD_COLOR, relief="flat")
    
    # Labels
    style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR, font=FONT_MAIN)
    style.configure("Card.TLabel", background=CARD_COLOR, foreground=TEXT_COLOR, font=FONT_MAIN)
    style.configure("Title.TLabel", background=CARD_COLOR, foreground=ACCENT_COLOR, font=FONT_TITLE)
    style.configure("Subtitle.TLabel", background=CARD_COLOR, foreground=TEXT_COLOR, font=FONT_SUBTITLE)
    style.configure("Muted.TLabel", background=CARD_COLOR, foreground=MUTED_TEXT, font=FONT_SMALL)
    style.configure("Success.TLabel", background=CARD_COLOR, foreground=SUCCESS_COLOR, font=FONT_MAIN)
    style.configure("Error.TLabel", background=CARD_COLOR, foreground=ERROR_COLOR, font=FONT_MAIN)
    style.configure("Price.TLabel", background=CARD_COLOR, foreground=TEXT_COLOR, font=FONT_PRICE)
    
    # Buttons
    style.configure("TButton", font=FONT_MAIN, background=ACCENT_COLOR, foreground="#000000",
                     borderwidth=0, padding=10)
    style.map("TButton", background=[("active", ACCENT_HOVER)])
    
    # Entries
    style.configure("TEntry", fieldbackground=INPUT_BG, foreground=TEXT_COLOR, 
                     borderwidth=0, padding=10, font=FONT_MAIN)
    
    return style
