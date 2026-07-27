"""
Módulo de Comunicación PC <-> ESP32-S3 (Interfaz Física)
Protocolo Serial Real con Trazabilidad TX ➔ y RX ◄.
"""
import time
import serial
import serial.tools.list_ports
import threading
import struct
import numpy as np

class ComunicacionESP32:
    def __init__(self, puerto="COM5", baudrate=115200):
        self.puerto = puerto
        self.baudrate = baudrate
        self.serial_conn = None
        self.conectado = False
        self.callback_log = None
        self.lock = threading.Lock()

    def obtener_puertos_disponibles(self):
        """Retorna una lista con los nombres de todos los puertos COM disponibles."""
        puertos = serial.tools.list_ports.comports()
        return [p.device for p in puertos] if puertos else ["COM5"]

    def conectar(self, puerto=None):
        """Establece conexión serial en un puerto específico."""
        if puerto:
            self.puerto = puerto
            
        with self.lock:
            try:
                if self.serial_conn and self.serial_conn.is_open:
                    self.serial_conn.close()

                self.serial_conn = serial.Serial(self.puerto, self.baudrate, timeout=2)
                time.sleep(0.3)
                self.serial_conn.reset_input_buffer()
                self.serial_conn.reset_output_buffer()

                # Ejecutar PING de prueba
                if self.callback_log:
                    self.callback_log(f"TX ➔ PING")
                self.serial_conn.write(b"PING\n")
                self.serial_conn.flush()
                res = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                if self.callback_log and res:
                    self.callback_log(f"RX ◄ {res}")

                if "PONG" in res or self.serial_conn.is_open:
                    self.conectado = True
                    if self.callback_log:
                        self.callback_log(f"[COM] Conexión física verificada en {self.puerto}.")
                    return True, self.puerto
                else:
                    self.conectado = False
                    if self.callback_log:
                        self.callback_log(f"[COM ERROR] {self.puerto} no respondió PONG.")
                    return False, self.puerto
            except Exception as e:
                self.conectado = False
                if self.callback_log:
                    self.callback_log(f"[COM ERROR] No se pudo abrir {self.puerto}: {e}")
                return False, self.puerto

    def auto_conectar(self, puerto_preferido=None):
        """
        Intenta conectar al puerto preferido. Si falla o está ocupado (ej. COM4 en Arduino IDE),
        escanea automáticamente los demás puertos disponibles (ej. COM5) hasta encontrar el ESP32-S3.
        """
        puertos = self.obtener_puertos_disponibles()
        if puerto_preferido and puerto_preferido in puertos:
            puertos.remove(puerto_preferido)
            puertos.insert(0, puerto_preferido)
        elif puerto_preferido:
            puertos.insert(0, puerto_preferido)

        for p in puertos:
            if self.callback_log:
                self.callback_log(f"[CONEXIÓN] Verificando puerto {p}...")
            exito, _ = self.conectar(p)
            if exito:
                return True, p

        return False, None

    def desconectar(self):
        """Cierra la conexión serial."""
        with self.lock:
            self.conectado = False
            if self.serial_conn and self.serial_conn.is_open:
                try:
                    self.serial_conn.close()
                except Exception:
                    pass
            if self.callback_log:
                self.callback_log("[COM] Desconectado.")

    def enviar_comando_oled(self, estado: str, texto_extra: str = ""):
        """Envía un cambio de estado al OLED."""
        if not self.conectado or not self.serial_conn:
            return False
        
        with self.lock:
            try:
                cmd = f"STATE:{estado.upper()}:{texto_extra}\n"
                self.serial_conn.write(cmd.encode('utf-8'))
                self.serial_conn.flush()
                if self.callback_log:
                    self.callback_log(f"TX ➔ {cmd.strip()}")
                return True
            except Exception as e:
                if self.callback_log:
                    self.callback_log(f"[COM ERROR] Error enviando comando OLED: {e}")
                return False

    def ejecutar_test_oled(self):
        """Envía OLED_TEST y espera a que el firmware responda OLED_TEST_OK."""
        if not self.conectado or not self.serial_conn:
            return False, "ESP32 no conectado"
            
        with self.lock:
            try:
                self.serial_conn.reset_input_buffer()
                if self.callback_log:
                    self.callback_log("TX ➔ OLED_TEST")
                self.serial_conn.write(b"OLED_TEST\n")
                self.serial_conn.flush()

                inicio = time.time()
                while time.time() - inicio < 14:
                    if self.serial_conn.in_waiting > 0:
                        linea = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                        if self.callback_log:
                            self.callback_log(f"RX ◄ {linea}")
                        if "OLED_TEST_OK" in linea:
                            return True, "OLED_TEST_OK"
                    time.sleep(0.1)

                return False, "TIMEOUT OLED_TEST"
            except Exception as e:
                return False, str(e)

    def ejecutar_test_audio(self):
        """Envía AUDIO_TEST para que el ESP32 emita un tono por el MAX98357A y devuelva AUDIO_TEST_OK."""
        if not self.conectado or not self.serial_conn:
            return False, "ESP32 no conectado"

        with self.lock:
            try:
                self.serial_conn.reset_input_buffer()
                if self.callback_log:
                    self.callback_log("TX ➔ AUDIO_TEST")
                self.serial_conn.write(b"AUDIO_TEST\n")
                self.serial_conn.flush()

                inicio = time.time()
                while time.time() - inicio < 5:
                    if self.serial_conn.in_waiting > 0:
                        linea = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                        if self.callback_log:
                            self.callback_log(f"RX ◄ {linea}")
                        if "AUDIO_TEST_OK" in linea:
                            return True, "AUDIO_TEST_OK"
                    time.sleep(0.1)

                return False, "TIMEOUT AUDIO_TEST"
            except Exception as e:
                return False, str(e)

    def capturar_audio_mic(self, duracion_sec=3):
        """Solicita al ESP32 grabar con INMP441 y enviar los bytes PCM por Serial."""
        if not self.conectado or not self.serial_conn:
            return None, "ESP32 no conectado"

        with self.lock:
            try:
                self.serial_conn.reset_input_buffer()
                if self.callback_log:
                    self.callback_log("TX ➔ MIC_START")
                self.serial_conn.write(b"MIC_START\n")
                self.serial_conn.flush()

                inicio = time.time()
                bytes_esperados = 0
                while time.time() - inicio < 6:
                    if self.serial_conn.in_waiting > 0:
                        linea = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                        if self.callback_log:
                            self.callback_log(f"RX ◄ {linea}")
                        if linea.startswith("MIC_DATA:"):
                            bytes_esperados = int(linea.split(":")[1])
                            break
                    time.sleep(0.05)

                if bytes_esperados <= 0:
                    return None, "No se recibió respuesta de audio"

                pcm_data = bytearray()
                while len(pcm_data) < bytes_esperados:
                    chunk = self.serial_conn.read(bytes_esperados - len(pcm_data))
                    if chunk:
                        pcm_data.extend(chunk)
                    else:
                        break

                audio_np = np.frombuffer(pcm_data, dtype=np.int16)
                rms = float(np.sqrt(np.mean(audio_np.astype(np.float64)**2)))
                max_peak = int(np.max(np.abs(audio_np))) if len(audio_np) > 0 else 0

                metrics = {
                    "duracion": len(audio_np) / 16000.0,
                    "rate": 16000,
                    "rms": rms,
                    "max_peak": max_peak,
                    "pcm_bytes": pcm_data
                }
                return metrics, "MIC_TEST_OK"
            except Exception as e:
                return None, str(e)

# Instancia global
esp32_comm = ComunicacionESP32()
