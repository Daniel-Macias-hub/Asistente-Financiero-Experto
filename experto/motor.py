from conocimiento.conceptos import buscar_conceptos_clave, obtener_concepto
from conocimiento.relaciones import obtener_relaciones
from experto.inferencia import evaluar_reglas
from experto.consultas import buscar_pregunta_frecuente
from experto.normalizador import normalizar_texto

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
