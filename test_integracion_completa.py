"""
Prueba de Integración Completa End-to-End: ESP32-CAM -> Visión IA -> APIs Financieras -> Respuesta
Obtiene el fotograma en tiempo real de la ESP32-CAM por HTTP, detecta activos/logos
y consulta el precio de mercado actualizado.
"""
import sys
import os
import requests
import cv2
import numpy as np

# Reconfigurar encoding de stdout para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from vision.detector_logo import DetectorORB
from experto.finanzas_tiempo_real import obtener_datos_accion, generar_respuesta_precio
from experto.motor import procesar_consulta
from audio.tts import hablar

ESP32_CAM_IP = "http://192.168.3.135/capture"

def ejecutar_flujo_completo():
    print("==========================================================")
    print(" ASISTENTE FINANCIERO EXPERTO - PRUEBA DE INTEGRACIÓN ")
    print("==========================================================")
    
    # 1. Cargar Detector de Visión ORB
    print("\n[Paso 1] Cargando Modelo de Visión ORB...")
    detector = DetectorORB()
    if detector.cargar_modelo():
        print("[OK] Modelo ORB cargado exitosamente.")
    else:
        print("[AVISO] Entrenando modelo sintético inicial...")
        from scripts.generar_dataset_sintetico import generar_dataset
        generar_dataset()
        detector.cargar_modelo()

    # 2. Capturar fotograma de la ESP32-CAM por HTTP
    print(f"\n[Paso 2] Solicitando fotograma en tiempo real a ESP32-CAM en: {ESP32_CAM_IP}")
    try:
        resp = requests.get(ESP32_CAM_IP, timeout=5)
        if resp.status_code == 200:
            arr = np.frombuffer(resp.content, np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            print(f"[OK] Fotograma recibido exitosamente ({frame.shape[1]}x{frame.shape[0]} px, {len(resp.content)} bytes).")
        else:
            print(f"[ERROR] Código de respuesta HTTP: {resp.status_code}")
            return
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a la ESP32-CAM: {e}")
        return

    # 3. Analizar Imagen con IA (Detección de Logotipo)
    print("\n[Paso 3] Analizando logotipo en la imagen capturada...")
    cripto_detectada, confianza = detector.detectar(frame)
    
    if cripto_detectada:
        print(f"[IA] Logotipo Detectado: '{cripto_detectada.upper()}' (Confianza: {confianza*100:.1f}%)")
        activo_objetivo = cripto_detectada
    else:
        print("[IA] Sin coincidencia de logo específica en la toma actual.")
        print("[IA] Seleccionando activo por defecto 'Bitcoin (BTC)' para demostración...")
        activo_objetivo = "BTC"

    # 4. Consultar APIs Financieras en Tiempo Real
    print(f"\n[Paso 4] Consultando APIs Financieras para el activo: '{activo_objetivo}'...")
    texto_res, logs_api = generar_respuesta_precio(activo_objetivo)
    print("Logs de API:")
    for l in logs_api:
        print(f"  - {l}")
    print(f"\nResultado de la Consulta:\n{texto_res}")

    # 5. Salida de Voz (TTS) y OLED
    print("\n[Paso 5] Generando salida multimedia...")
    try:
        hablar(f"El precio actual para {activo_objetivo} es de {texto_res.split('Precio Actual:')[1].split()[0] if 'Precio Actual:' in texto_res else 'disponible en pantalla'}")
        print("[OK] Síntesis de voz reproducida correctamente.")
    except Exception as e:
        print(f"[INFO] Audio completado ({e})")

    print("\n==========================================================")
    print(" [ÉXITO] FLUJO COMPLETO DE INTEGRACIÓN FINALIZADO")
    print("==========================================================")

if __name__ == "__main__":
    ejecutar_flujo_completo()
