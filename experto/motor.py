from conocimiento.conceptos import buscar_conceptos_clave, obtener_concepto
from conocimiento.relaciones import obtener_relaciones
from experto.inferencia import evaluar_reglas
from experto.consultas import buscar_pregunta_frecuente
from experto.normalizador import normalizar_texto
from experto.finanzas_tiempo_real import generar_respuesta_precio
import re

def procesar_consulta(texto_usuario):
    """
    Función principal del motor experto.
    Recibe texto del usuario y devuelve una respuesta generada a partir de 
    encadenamiento de reglas, búsqueda de conceptos y relaciones.
    """
    log_inferencia = []
    
    # 0. Normalización del Texto
    texto_original = texto_usuario
    texto_usuario = normalizar_texto(texto_usuario)
    if texto_usuario != texto_original.lower():
        log_inferencia.append(f"Texto normalizado a: '{texto_usuario}'")
        
    # 0.5. Búsqueda en Tiempo Real (yfinance)
    # Detectar patrones de precio o tickers directo (ej. "precio de MSFT", "cotizacion de AAPL", "MSFT")
    match_precio = re.search(
        r'\b(?:precio de|cotizacion de|cotización de|valor de|cuanto vale|cuánto vale|accion de|acción de|ticker)\s*(?:la accion de|la acción de|el ticker|de|el)?\s*([a-zA-Z]+)\b', 
        texto_usuario
    )
    
    ticker_candidato = None
    es_busqueda_explicita = False
    
    if match_precio:
        ticker_candidato = match_precio.group(1).upper()
        es_busqueda_explicita = True
    else:
        # Si es una sola palabra de 2 a 5 letras que no es un concepto ni un sinónimo en la BD
        palabras = texto_usuario.strip().split()
        if len(palabras) == 1 and palabras[0].isalpha() and 2 <= len(palabras[0]) <= 5:
            # Comprobar si existe en la BD
            if not obtener_concepto(palabras[0]):
                ticker_candidato = palabras[0].upper()
                es_busqueda_explicita = False

    if ticker_candidato:
        log_inferencia.append(f"Intención de mercado en tiempo real detectada para ticker: {ticker_candidato}")
        res, log_yf = generar_respuesta_precio(ticker_candidato)
        # Protección ante log_yf vacío (evita IndexError)
        ultimo_log = log_yf[-1] if log_yf else ""
        if "No se pudieron obtener datos" not in ultimo_log or es_busqueda_explicita:
            log_inferencia.extend(log_yf)
            return res, log_inferencia

        
    # 1. Búsqueda Directa en Preguntas Frecuentes
    respuesta_rapida = buscar_pregunta_frecuente(texto_usuario)
    if respuesta_rapida:
        log_inferencia.append("Se encontró respuesta directa en Preguntas Frecuentes.")
        return respuesta_rapida, log_inferencia
        
    # 2. Motor de Inferencia: Evaluar Reglas (Encadenamiento hacia adelante simple)
    conclusiones = evaluar_reglas(texto_usuario)
    if conclusiones:
        log_inferencia.append(f"Reglas disparadas. Conclusiones aplicadas: {', '.join(conclusiones)}")
        # Enriquecer el texto de búsqueda con las conclusiones de las reglas
        texto_usuario = texto_usuario + " " + " ".join(conclusiones)
        
    # 3. Extracción de Conceptos Clave (después de aplicar reglas)
    conceptos_encontrados = buscar_conceptos_clave(texto_usuario)
    if not conceptos_encontrados:
        log_inferencia.append("No se identificaron conceptos clave en la consulta.")
        if conclusiones:
            return "Según mis reglas: " + ". ".join(conclusiones), log_inferencia
        return "Lo siento, no tengo conocimiento sobre eso. Puedes entrenarme agregando este concepto.", log_inferencia
        
    log_inferencia.append(f"Conceptos identificados para búsqueda: {', '.join(conceptos_encontrados)}")
    
    # 4. Elaboración de Respuesta Dinámica
    respuesta_partes = []
    
    if conclusiones:
        respuesta_partes.append("Basado en el análisis de reglas: " + ". ".join(conclusiones) + ".")

    for concepto in conceptos_encontrados:
        definicion = obtener_concepto(concepto)
        if definicion:
            respuesta_partes.append(f"• {concepto.upper()}: {definicion}")
            
        # Expansión Semántica (Relaciones)
        relaciones = obtener_relaciones(concepto)
        if relaciones:
            desc_relaciones = ", ".join([f"{r['tipo_relacion']} {r['destino']}" for r in relaciones])
            respuesta_partes.append(f"  Nota: Está relacionado de la siguiente forma -> {desc_relaciones}.")
            log_inferencia.append(f"Se expandió semánticamente el concepto '{concepto}' mostrando sus relaciones.")
            
    respuesta_final = "\n".join(respuesta_partes)
    return respuesta_final, log_inferencia
