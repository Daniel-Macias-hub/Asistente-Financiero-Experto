"""
Entrenamiento visual: genera y gestiona descriptores ORB para el dataset de logotipos.
Permite aprendizaje incremental al agregar nuevas imágenes y recalcular descriptores.
"""
import os
import pickle
import cv2
import numpy as np
from config import (
    DATASET_PATH, MODELOS_VISION_PATH, ORB_DESCRIPTORS_FILE, ORB_N_FEATURES
)


def reentrenar_descriptores(ruta_dataset=None):
    """
    Recorre el dataset de logotipos y genera descriptores ORB para cada clase.
    Guarda los resultados en un archivo pickle.
    
    Estructura esperada del dataset:
        dataset_crypto/
            bitcoin/
                logo1.png
                logo2.jpg
                ...
            ethereum/
                logo1.png
                ...
    
    Args:
        ruta_dataset: Ruta al directorio del dataset. Si None, usa la ruta por defecto.
    
    Returns:
        tuple (exito, mensaje) donde exito es True/False.
    """
    ruta_dataset = ruta_dataset or DATASET_PATH
    
    if not os.path.exists(ruta_dataset):
        return False, f"El directorio del dataset no existe: {ruta_dataset}"
    
    orb = cv2.ORB_create(nfeatures=ORB_N_FEATURES)
    descriptores_db = {}
    
    clases = [d for d in os.listdir(ruta_dataset) 
              if os.path.isdir(os.path.join(ruta_dataset, d))]
    
    if not clases:
        return False, "No se encontraron carpetas de clases en el dataset."
    
    total_imagenes = 0
    
    for clase in clases:
        clase_dir = os.path.join(ruta_dataset, clase)
        descriptores_clase = []
        
        extensiones = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')
        imagenes = [f for f in os.listdir(clase_dir) 
                    if f.lower().endswith(extensiones)]
        
        for img_nombre in imagenes:
            img_path = os.path.join(clase_dir, img_nombre)
            
            try:
                img = cv2.imread(img_path)
                if img is None:
                    print(f"  [!] No se pudo leer: {img_path}")
                    continue
                
                # Preprocesar: escala de grises y resize
                gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                gris = cv2.resize(gris, (300, 300))
                
                # Extraer descriptores
                kp, desc = orb.detectAndCompute(gris, None)
                
                if desc is not None:
                    descriptores_clase.append(desc)
                    total_imagenes += 1
                else:
                    print(f"  [!] Sin features detectadas en: {img_nombre}")
            except Exception as e:
                print(f"  [!] Error procesando {img_nombre}: {e}")
        
        if descriptores_clase:
            descriptores_db[clase.lower()] = descriptores_clase
            print(f"  ✓ {clase}: {len(descriptores_clase)} imágenes procesadas")
        else:
            print(f"  ✗ {clase}: sin descriptores válidos")
    
    if not descriptores_db:
        return False, "No se pudieron generar descriptores para ninguna clase."
    
    # Crear directorio de modelos si no existe
    os.makedirs(MODELOS_VISION_PATH, exist_ok=True)
    
    # Guardar descriptores
    with open(ORB_DESCRIPTORS_FILE, 'wb') as f:
        pickle.dump(descriptores_db, f)
    
    n_clases = len(descriptores_db)
    mensaje = f"Entrenamiento completado: {n_clases} clases, {total_imagenes} imágenes procesadas."
    print(f"[Entrenamiento] {mensaje}")
    print(f"[Entrenamiento] Modelo guardado en: {ORB_DESCRIPTORS_FILE}")
    
    return True, mensaje


def agregar_clase(nombre, lista_imagenes_paths):
    """
    Agrega una nueva clase (criptomoneda) al dataset y reentrena.
    
    Args:
        nombre: Nombre de la criptomoneda (será el nombre de la carpeta).
        lista_imagenes_paths: Lista de rutas absolutas a imágenes del logotipo.
    
    Returns:
        tuple (exito, mensaje).
    """
    import shutil
    
    nombre_lower = nombre.lower().strip()
    clase_dir = os.path.join(DATASET_PATH, nombre_lower)
    
    # Crear directorio si no existe
    os.makedirs(clase_dir, exist_ok=True)
    
    # Copiar imágenes
    copiadas = 0
    for i, ruta_img in enumerate(lista_imagenes_paths):
        if not os.path.exists(ruta_img):
            print(f"  [!] Imagen no encontrada: {ruta_img}")
            continue
        
        ext = os.path.splitext(ruta_img)[1]
        destino = os.path.join(clase_dir, f"logo_{i+1}{ext}")
        
        try:
            shutil.copy2(ruta_img, destino)
            copiadas += 1
        except Exception as e:
            print(f"  [!] Error copiando {ruta_img}: {e}")
    
    if copiadas == 0:
        return False, "No se pudo copiar ninguna imagen."
    
    # Reentrenar con todo el dataset
    exito, msg = reentrenar_descriptores()
    
    if exito:
        return True, f"Clase '{nombre}' agregada con {copiadas} imágenes. {msg}"
    else:
        return False, f"Imágenes copiadas pero error al reentrenar: {msg}"


def agregar_imagenes_a_clase(nombre, lista_imagenes_paths):
    """
    Agrega imágenes adicionales a una clase existente y reentrena.
    
    Args:
        nombre: Nombre de la criptomoneda.
        lista_imagenes_paths: Lista de rutas a imágenes adicionales.
    
    Returns:
        tuple (exito, mensaje).
    """
    nombre_lower = nombre.lower().strip()
    clase_dir = os.path.join(DATASET_PATH, nombre_lower)
    
    if not os.path.exists(clase_dir):
        return agregar_clase(nombre, lista_imagenes_paths)
    
    # Contar imágenes existentes para numerar las nuevas
    existentes = len([f for f in os.listdir(clase_dir) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp'))])
    
    import shutil
    copiadas = 0
    for i, ruta_img in enumerate(lista_imagenes_paths):
        if not os.path.exists(ruta_img):
            continue
        ext = os.path.splitext(ruta_img)[1]
        destino = os.path.join(clase_dir, f"logo_{existentes + i + 1}{ext}")
        try:
            shutil.copy2(ruta_img, destino)
            copiadas += 1
        except Exception:
            continue
    
    if copiadas == 0:
        return False, "No se pudieron copiar imágenes adicionales."
    
    exito, msg = reentrenar_descriptores()
    if exito:
        return True, f"{copiadas} imágenes agregadas a '{nombre}'. {msg}"
    return False, f"Imágenes agregadas pero error al reentrenar: {msg}"


def obtener_clases_dataset():
    """
    Lista las clases disponibles en el dataset con conteo de imágenes.
    
    Returns:
        dict {nombre_clase: n_imagenes}
    """
    if not os.path.exists(DATASET_PATH):
        return {}
    
    resultado = {}
    extensiones = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')
    
    for d in sorted(os.listdir(DATASET_PATH)):
        clase_dir = os.path.join(DATASET_PATH, d)
        if os.path.isdir(clase_dir):
            n_imgs = len([f for f in os.listdir(clase_dir) 
                          if f.lower().endswith(extensiones)])
            resultado[d] = n_imgs
    
    return resultado


if __name__ == "__main__":
    print("=== Entrenamiento Visual de Logotipos ===")
    exito, msg = reentrenar_descriptores()
    print(msg)
    if exito:
        clases = obtener_clases_dataset()
        print(f"\nClases en el dataset:")
        for nombre, n in clases.items():
            print(f"  {nombre}: {n} imágenes")
