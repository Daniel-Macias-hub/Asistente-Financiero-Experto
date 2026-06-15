import pyttsx3

# Inicializamos el motor globalmente para no recrearlo cada vez
engine = pyttsx3.init()

# Configuración básica (intentar buscar voz en español)
voces = engine.getProperty('voices')
for voz in voces:
    if "spanish" in voz.name.lower() or "es" in voz.languages:
        engine.setProperty('voice', voz.id)
        break
engine.setProperty('rate', 150) # Velocidad de habla

def hablar(texto):
    """
    Toma una cadena de texto y la reproduce a través de los altavoces.
    Funciona completamente offline.
    """
    engine.say(texto)
    engine.runAndWait()
