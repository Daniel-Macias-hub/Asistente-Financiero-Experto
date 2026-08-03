from conocimiento.reglas import obtener_todas_las_reglas

def evaluar_reglas(texto_usuario):
    """
    Evalúa las reglas cargadas desde la BD para encontrar encadenamientos lógicos.
    Retorna una lista de conclusiones aplicables basadas en las reglas que se cumplen.
    """
    reglas = obtener_todas_las_reglas()
    texto_lower = texto_usuario.lower()
    
    conclusiones_aplicables = []
    
    for regla in reglas:
        condicion = regla['condicion'].lower()
        # Lógica de inferencia simple: si todas las palabras clave de la condición
        # están presentes en el input del usuario, la regla dispara.
        palabras_condicion = condicion.split()
        if all(palabra in texto_lower for palabra in palabras_condicion):
            conclusiones_aplicables.append(regla['conclusion'])
            
    return conclusiones_aplicables
