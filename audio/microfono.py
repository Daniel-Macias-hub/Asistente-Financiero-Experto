# Este archivo se incluye para cumplir la estructura solicitada.
# La gestión del micrófono se ha integrado directamente en stt.py
# usando la librería sounddevice por su eficiencia y compatibilidad.

def probar_microfono():
    import sounddevice as sd
    print("Dispositivos de audio disponibles:")
    print(sd.query_devices())
    return True

if __name__ == "__main__":
    probar_microfono()
