"""
Módulo de Comunicación PC <-> ESP32-S3 (Interfaz Física)
Conexión serial a la PCB (COM11 por defecto) con reintentos y trazabilidad transparente.
"""
import time
import serial
import serial.tools.list_ports
import threading
import struct
import numpy as np

class ComunicacionESP32:
    def __init__(self, puerto="COM11", baudrate=115200):
        self.puerto = puerto
        self.baudrate = baudrate
        self.serial_conn = None
        self.conectado = False
        self.callback_log = None
        self.lock = threading.Lock()
        self.cancelar_flag = False

    def detener_operacion(self):
        """Detiene de inmediato cualquier transferencia de audio o prueba en curso."""
        self.cancelar_flag = True
        try:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.write(b"STOP\nSTATE:IDLE:\n")
                self.serial_conn.flush()
                time.sleep(0.1)
                self.serial_conn.reset_input_buffer()
                self.serial_conn.reset_output_buffer()
                if self.callback_log:
                    self.callback_log("[SISTEMA] 🛑 PRUEBA CANCELADA POR EL USUARIO.")
        except Exception as e:
            if self.callback_log:
                self.callback_log(f"[STOP ERR] {e}")
        return True, "CANCELADO"

    def obtener_puertos_disponibles(self):
        """Retorna una lista con los nombres de todos los puertos COM disponibles."""
        puertos = serial.tools.list_ports.comports()
        return [p.device for p in puertos] if puertos else ["COM11"]

    def conectar(self, puerto="COM11"):
        """Establece conexión serial exclusivamente en el puerto indicado (defecto COM11)."""
        if puerto:
            self.puerto = puerto

        with self.lock:
            try:
                if self.serial_conn and self.serial_conn.is_open:
                    self.serial_conn.close()

                # 1. Abrir puerto con timeout adecuado (3 segundos)
                self.serial_conn = serial.Serial(self.puerto, self.baudrate, timeout=3)

                # 2. Retardo de inicialización de 800 ms tras abrir el puerto serie
                time.sleep(0.8)

                # 3. Leer y consumir cualquier mensaje de arranque (READY, [BOOT], [FIRMWARE])
                boot_bytes = b""
                if self.serial_conn.in_waiting > 0:
                    boot_bytes = self.serial_conn.read_all()
                    if self.callback_log:
                        self.callback_log(f"[COM BOOT READ] Bytes de arranque leídos: {repr(boot_bytes)}")

                # 4. Vaciar buffers limpio
                self.serial_conn.reset_input_buffer()
                self.serial_conn.reset_output_buffer()

                # 5. Enviar PING estrictamente terminado en \n y verificar PONG
                confirmado = False
                for intento in range(3):
                    cmd_bytes = b"PING\n"
                    if self.callback_log:
                        self.callback_log(f"TX ➔ {repr(cmd_bytes)}")
                    
                    self.serial_conn.write(cmd_bytes)
                    self.serial_conn.flush()

                    t0 = time.time()
                    resp_acumulada = ""
                    repl_detectado = False
                    while time.time() - t0 < 3.0:
                        if self.serial_conn.in_waiting > 0:
                            raw_line = self.serial_conn.readline()
                            line_str = raw_line.decode('utf-8', errors='ignore').strip()
                            if self.callback_log:
                                self.callback_log(f"RX ◄ {repr(raw_line)} -> '{line_str}'")
                            
                            if "PONG" in line_str or "READY" in line_str:
                                confirmado = True
                                break
                            elif ">>>" in line_str or "NameError" in line_str:
                                repl_detectado = True
                        time.sleep(0.05)

                    if confirmado:
                        break
                    elif repl_detectado:
                        if self.callback_log:
                            self.callback_log("[COM REPL] MicroPython en consola '>>> '. Enviando Ctrl+D (Soft Reset) para ejecutar main.py...")
                        # Enviar Ctrl+D (Soft Reset) para forzar la ejecución de main.py
                        self.serial_conn.write(b"\x04\nimport main\n")
                        self.serial_conn.flush()
                        time.sleep(1.0)
                    else:
                        time.sleep(0.3)

                if confirmado:
                    self.conectado = True
                    if self.callback_log:
                        self.callback_log(f"[COM] Conexión física verificada exitosamente en {self.puerto}.")
                    return True, self.puerto
                else:
                    self.conectado = False
                    if self.callback_log:
                        self.callback_log(f"[COM ERROR] {self.puerto} abrió pero no respondió PONG tras PING.")
                    return False, self.puerto

            except serial.SerialException as se:
                self.conectado = False
                msg = str(se)
                if "PermissionError" in msg or "Access is denied" in msg:
                    err_hint = f"[COM ERROR] El puerto {self.puerto} está ocupado por Thonny IDE. Presiona 'Stop' o cierra Thonny."
                else:
                    err_hint = f"[COM ERROR] No se pudo abrir {self.puerto}: {se}"

                if self.callback_log:
                    self.callback_log(err_hint)
                return False, self.puerto
            except Exception as e:
                self.conectado = False
                if self.callback_log:
                    self.callback_log(f"[COM ERROR] Fallo inesperado en {self.puerto}: {e}")
                return False, self.puerto

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
        """Envía un cambio de estado al OLED terminado estrictamente en \n."""
        if not self.conectado or not self.serial_conn:
            return False

        with self.lock:
            try:
                cmd_str = f"STATE:{estado.upper()}:{texto_extra}\n"
                cmd_bytes = cmd_str.encode('utf-8')
                self.serial_conn.write(cmd_bytes)
                self.serial_conn.flush()
                if self.callback_log:
                    self.callback_log(f"TX ➔ {repr(cmd_bytes)}")
                return True
            except Exception as e:
                if self.callback_log:
                    self.callback_log(f"[COM ERROR] Error enviando comando OLED: {e}")
                return False

    def ejecutar_test_oled(self):
        """Envía OLED_TEST\\n y espera a que el firmware responda OLED_TEST_OK."""
        if not self.conectado or not self.serial_conn:
            return False, "ESP32 no conectado"

        with self.lock:
            try:
                self.serial_conn.reset_input_buffer()
                cmd_bytes = b"OLED_TEST\n"
                if self.callback_log:
                    self.callback_log(f"TX ➔ {repr(cmd_bytes)}")
                self.serial_conn.write(cmd_bytes)
                self.serial_conn.flush()

                inicio = time.time()
                while time.time() - inicio < 6:
                    if self.serial_conn.in_waiting > 0:
                        raw_line = self.serial_conn.readline()
                        linea = raw_line.decode('utf-8', errors='ignore').strip()
                        if self.callback_log and raw_line:
                            self.callback_log(f"RX ◄ {repr(raw_line)} -> '{linea}'")
                        if "OLED_TEST_OK" in linea:
                            return True, "OLED_TEST_OK"
                    time.sleep(0.05)

                return False, "TIMEOUT OLED_TEST"
            except Exception as e:
                return False, str(e)

    def ejecutar_test_audio(self):
        """Envía AUDIO_TEST\\n para que el ESP32 emita un tono por el MAX98357A y devuelva AUDIO_TEST_OK."""
        if not self.conectado or not self.serial_conn:
            return False, "ESP32 no conectado"

        with self.lock:
            try:
                self.serial_conn.reset_input_buffer()
                cmd_bytes = b"AUDIO_TEST\n"
                if self.callback_log:
                    self.callback_log(f"TX ➔ {repr(cmd_bytes)}")
                self.serial_conn.write(cmd_bytes)
                self.serial_conn.flush()

                inicio = time.time()
                while time.time() - inicio < 5:
                    if self.serial_conn.in_waiting > 0:
                        raw_line = self.serial_conn.readline()
                        linea = raw_line.decode('utf-8', errors='ignore').strip()
                        if self.callback_log and raw_line:
                            self.callback_log(f"RX ◄ {repr(raw_line)} -> '{linea}'")
                        if "AUDIO_TEST_OK" in linea:
                            return True, "AUDIO_TEST_OK"
                    time.sleep(0.05)

                return False, "TIMEOUT AUDIO_TEST"
            except Exception as e:
                return False, str(e)

    def reproducir_audio_bocina_pcm(self, pcm_bytes: bytes):
        """Transmite bytes PCM codificados en Base64 al ESP32-S3 en estricta sincronía."""
        if not self.conectado or not self.serial_conn or not pcm_bytes:
            return False, "ESP32 no conectado o sin audio"

        self.cancelar_flag = False
        with self.lock:
            try:
                self.serial_conn.reset_input_buffer()
                cmd_str = f"AUDIO_PLAY:{len(pcm_bytes)}\n"
                cmd_bytes = cmd_str.encode('utf-8')
                if self.callback_log:
                    self.callback_log(f"TX ➔ {repr(cmd_bytes)}")
                self.serial_conn.write(cmd_bytes)
                self.serial_conn.flush()

                t0 = time.time()
                ready = False
                while time.time() - t0 < 4:
                    if self.cancelar_flag:
                        return False, "CANCELADO"
                    if self.serial_conn.in_waiting > 0:
                        raw_line = self.serial_conn.readline()
                        linea = raw_line.decode('utf-8', errors='ignore').strip()
                        if self.callback_log and raw_line:
                            self.callback_log(f"RX ◄ {repr(raw_line)} -> '{linea}'")
                        if "AUDIO_PLAY_READY" in linea:
                            ready = True
                            break
                    time.sleep(0.05)

                if not ready:
                    return False, "TIMEOUT AUDIO_PLAY_READY"

                import base64
                # Chunks de 512 bytes con pacing para evitar desbordamiento del búfer FIFO UART del ESP32
                chunk_size = 512
                for idx in range(0, len(pcm_bytes), chunk_size):
                    if self.cancelar_flag:
                        self.serial_conn.write(b"STOP\n")
                        self.serial_conn.flush()
                        return False, "CANCELADO"
                    chunk = pcm_bytes[idx : idx + chunk_size]
                    b64_str = base64.b64encode(chunk).decode('utf-8')
                    self.serial_conn.write(f"{b64_str}\n".encode('utf-8'))
                    self.serial_conn.flush()
                    time.sleep(0.005)

                self.serial_conn.write(b"AUDIO_PLAY_END\n")
                self.serial_conn.flush()

                # Esperar AUDIO_PLAY_OK — timeout = tamaño del audio + 5 segundos de margen
                dur_audio_sec = len(pcm_bytes) / (16000 * 2)
                timeout_ok = dur_audio_sec + 5.0
                t_ok = time.time()
                while time.time() - t_ok < timeout_ok:
                    if self.cancelar_flag:
                        return False, "CANCELADO"
                    if self.serial_conn.in_waiting > 0:
                        raw_line = self.serial_conn.readline()
                        linea = raw_line.decode('utf-8', errors='ignore').strip()
                        if self.callback_log and raw_line:
                            self.callback_log(f"RX ◄ {repr(raw_line)} -> '{linea}'")
                        if "AUDIO_PLAY_OK" in linea:
                            break
                    time.sleep(0.05)

                return True, "AUDIO_PLAY_OK"
            except Exception as e:
                return False, str(e)

    def capturar_audio_mic(self, duracion_sec=5):
        """Dispara la prueba local completa guiada de 5s grabación/reproducción en RAM del ESP32-S3."""
        if not self.conectado or not self.serial_conn:
            return None, "ESP32 no conectado"

        self.cancelar_flag = False
        with self.lock:
            try:
                self.serial_conn.reset_input_buffer()
                cmd_bytes = b"MIC_TEST\n"
                if self.callback_log:
                    self.callback_log(f"TX ➔ {repr(cmd_bytes)}")
                self.serial_conn.write(cmd_bytes)
                self.serial_conn.flush()

                inicio = time.time()
                rms_real = 0.0
                min_real = 0
                max_real = 0
                while time.time() - inicio < 22:
                    if self.cancelar_flag:
                        return None, "CANCELADO"
                    if self.serial_conn.in_waiting > 0:
                        raw_line = self.serial_conn.readline()
                        linea = raw_line.decode('utf-8', errors='ignore').strip()
                        if self.callback_log and raw_line:
                            self.callback_log(f"RX ◄ {repr(raw_line)} -> '{linea}'")
                        # Parsear métricas reales del firmware: [STEP 5.1] ... RMS=XXXX.XX
                        if "[STEP 5.1]" in linea and "RMS=" in linea:
                            try:
                                rms_real = float(linea.split("RMS=")[1].split(",")[0].strip())
                            except Exception:
                                pass
                            try:
                                min_real = int(linea.split("Min=")[1].split(",")[0].strip())
                            except Exception:
                                pass
                            try:
                                max_real = int(linea.split("Max=")[1].split(",")[0].strip())
                            except Exception:
                                pass
                        if "MIC_TEST_OK" in linea:
                            metrics = {
                                "duracion": 5.0,
                                "rate": 16000,
                                "rms": rms_real,
                                "max_peak": max_real,
                                "min_peak": min_real,
                                "pcm_bytes": b"OK"
                            }
                            return metrics, "MIC_TEST_OK"
                    time.sleep(0.05)

                return None, "TIMEOUT MIC_TEST"
            except Exception as e:
                return None, str(e)




# Instancia global
esp32_comm = ComunicacionESP32()
