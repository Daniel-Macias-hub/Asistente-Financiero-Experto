import tkinter as tk
import os
from interfaz.app import AsistenteApp
from conocimiento.database import inicializar_db
from inicializar_datos import pre_cargar_conocimiento

def main():
    # 1. Asegurar que la base de datos existe
    print("Inicializando base de datos...")
    inicializar_db()
    
    # 2. Cargar datos de prueba si es la primera vez
    print("Verificando conocimiento inicial...")
    pre_cargar_conocimiento()
    
    # 3. Lanzar la interfaz gráfica
    print("Iniciando Interfaz Gráfica...")
    root = tk.Tk()
    app = AsistenteApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
