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

    def es_puerto_bluetooth(self, p_info):
        """Devuelve True si el puerto COM es un dispositivo serie por Bluetooth."""
        desc = (p_info.description or "").lower()
        hwid = (p_info.hwid or "").lower()
        dev = (p_info.device or "").lower()
        keywords_bt = ["bluetooth", "bthenum", "vínculo bluetooth", "vinculo bluetooth", "serie estándar sobre"]
        return any(k in desc or k in hwid for k in keywords_bt)

    def obtener_puertos_disponibles(self, incluir_bluetooth=False):
        """
        Retorna una lista con los nombres de todos los puertos COM disponibles,
        excluyendo por defecto los puertos virtuales Bluetooth y priorizando adaptadores USB-Serial (CH343, CH340, CP210x, etc.).
        """
        puertos = serial.tools.list_ports.comports()
        if not puertos:
            return ["COM11"]

        usb_ports = []
        otros_ports = []
        for p in puertos:
            if not incluir_bluetooth and self.es_puerto_bluetooth(p):
                continue
            desc = (p.description or "").upper()
            hwid = (p.hwid or "").upper()
            # Prioridad a chips USB-Serial conocidos
            if any(k in desc or k in hwid for k in ["CH343", "CH340", "CP210", "FTDI", "USB", "ESP32", "SERIAL"]):
                usb_ports.append(p.device)
            else:
                otros_ports.append(p.device)

        resultado = usb_ports + otros_ports
        return resultado if resultado else [p.device for p in puertos if incluir_bluetooth or not self.es_puerto_bluetooth(p)] or ["COM11"]

    def autodetectar_puerto_esp32(self, puerto_excluir=None):
        """
        Escanea automáticamente todos los puertos USB serie físicos activos buscando responder PONG al PING.
        Retorna (bool_exito, str_puerto_hallado).
        """
        if self.callback_log:
            self.callback_log("[AUTO-DETECT] Buscando ESP32-S3 en los puertos USB serie disponibles...")

        puertos_cand = serial.tools.list_ports.comports()
        for p_info in puertos_cand:
            p_dev = p_info.device
            if puerto_excluir and p_dev == puerto_excluir:
                continue
            if self.es_puerto_bluetooth(p_info):
                continue

            if self.callback_log:
                self.callback_log(f"[AUTO-DETECT] Probando puerto USB {p_dev} ({p_info.description})...")

            try:
                with serial.Serial(p_dev, self.baudrate, timeout=1.0) as s:
                    time.sleep(0.4)
                    s.reset_input_buffer()
                    s.reset_output_buffer()
                    s.write(b"PING\n")
                    s.flush()

                    t0 = time.time()
                    confirmado = False
                    repl_detectado = False
                    while time.time() - t0 < 1.2:
                        if s.in_waiting > 0:
                            raw = s.readline()
                            linea = raw.decode('utf-8', errors='ignore').strip()
                            if "PONG" in linea or "READY" in linea:
                                confirmado = True
                                break
                            elif ">>>" in linea or "NameError" in linea:
                                repl_detectado = True
                        time.sleep(0.04)

                    if not confirmado and repl_detectado:
                        s.write(b"\x04\nimport main\n")
                        s.flush()
                        time.sleep(0.8)
                        s.write(b"PING\n")
                        s.flush()
                        t0 = time.time()
                        while time.time() - t0 < 1.0:
                            if s.in_waiting > 0:
                                linea = s.readline().decode('utf-8', errors='ignore').strip()
                                if "PONG" in linea or "READY" in linea:
                                    confirmado = True
                                    break
                            time.sleep(0.04)

                    if confirmado:
                        if self.callback_log:
                            self.callback_log(f"[AUTO-DETECT] ¡ESP32-S3 respondio PONG en {p_dev}!")
                        return True, p_dev
            except Exception as e:
                pass

        if self.callback_log:
            self.callback_log("[AUTO-DETECT] No se detectó respuesta PONG en ningún puerto USB serie.")
        return False, None

    def conectar(self, puerto=None):
        """
        Establece conexión serial. Si el puerto indicado es Bluetooth o falla,
        activa automáticamente la detección de puertos USB.
        """
        # Si se solicita AUTO o puerto no especificado
        if not puerto or puerto == "AUTO":
            ok_auto, p_auto = self.autodetectar_puerto_esp32()
            if ok_auto:
                puerto = p_auto
            else:
                puerto = self.obtener_puertos_disponibles()[0]

        # Verificar si el puerto solicitado es Bluetooth
        puertos_all = serial.tools.list_ports.comports()
        es_bt = False
        for p_info in puertos_all:
            if p_info.device == puerto and self.es_puerto_bluetooth(p_info):
                es_bt = True
                break

        if es_bt:
            if self.callback_log:
                self.callback_log(f"[COM ADVERTENCIA] {puerto} es un puerto Bluetooth (no USB). Redirigiendo a auto-detección USB...")
            ok_auto, p_auto = self.autodetectar_puerto_esp32()
            if ok_auto:
                puerto = p_auto
            else:
                disps = self.obtener_puertos_disponibles()
                if disps and disps[0] != puerto:
                    puerto = disps[0]

        self.puerto = puerto

        with self.lock:
            try:
                if self.serial_conn and self.serial_conn.is_open:
                    self.serial_conn.close()

                # 1. Abrir puerto con timeout adecuado (1.5 segundos)
                self.serial_conn = serial.Serial(self.puerto, self.baudrate, timeout=1.5)

                # 2. Retardo de inicialización de 600 ms tras abrir el puerto serie
                time.sleep(0.6)

                # 3. Leer y consumir cualquier mensaje de arranque
                boot_bytes = b""
                if self.serial_conn.in_waiting > 0:
                    boot_bytes = self.serial_conn.read_all()
                    if self.callback_log:
                        self.callback_log(f"[COM BOOT READ] Bytes de arranque leídos: {repr(boot_bytes)}")

                # 4. Vaciar buffers limpio
                self.serial_conn.reset_input_buffer()
                self.serial_conn.reset_output_buffer()

                # 5. Enviar PING y verificar PONG con timeout optimizado
                confirmado = False
                for intento in range(2):
                    cmd_bytes = b"PING\n"
                    if self.callback_log:
                        self.callback_log(f"TX -> {repr(cmd_bytes)}")

                    self.serial_conn.write(cmd_bytes)
                    self.serial_conn.flush()

                    t0 = time.time()
                    repl_detectado = False
                    while time.time() - t0 < 1.2:
                        if self.serial_conn.in_waiting > 0:
                            raw_line = self.serial_conn.readline()
                            line_str = raw_line.decode('utf-8', errors='ignore').strip()
                            if self.callback_log:
                                self.callback_log(f"RX <- {repr(raw_line)} -> '{line_str}'")

                            if "PONG" in line_str or "READY" in line_str:
                                confirmado = True
                                break
                            elif ">>>" in line_str or "NameError" in line_str:
                                repl_detectado = True
                        time.sleep(0.04)

                    if confirmado:
                        break
                    elif repl_detectado:
                        if self.callback_log:
                            self.callback_log("[COM REPL] MicroPython en consola '>>> '. Enviando Ctrl+D (Soft Reset)...")
                        self.serial_conn.write(b"\x04\nimport main\n")
                        self.serial_conn.flush()
                        time.sleep(0.8)
                    else:
                        time.sleep(0.2)

                if confirmado:
                    self.conectado = True
                    if self.callback_log:
                        self.callback_log(f"[COM] Conexión física verificada exitosamente en {self.puerto}.")
                    return True, self.puerto
                else:
                    self.conectado = False
                    if self.callback_log:
                        self.callback_log(f"[COM ERROR] {self.puerto} no respondió PONG tras PING.")

                    # Intento final de rescate: auto-detectar si otro puerto USB responde
                    if self.callback_log:
                        self.callback_log("[COM RESCATE] Intentando autodetectar el ESP32-S3 en otros puertos...")
                    ok_res, p_res = self.autodetectar_puerto_esp32(puerto_excluir=self.puerto)
                    if ok_res:
                        self.serial_conn.close()
                        self.serial_conn = serial.Serial(p_res, self.baudrate, timeout=1.5)
                        self.puerto = p_res
                        self.conectado = True
                        if self.callback_log:
                            self.callback_log(f"[COM RESCATE] ¡Conectado exitosamente en puerto rescatado {p_res}!")
                        return True, p_res

                    return False, self.puerto

            except serial.SerialException as se:
                self.conectado = False
                msg = str(se)
                if "PermissionError" in msg or "Access is denied" in msg:
                    err_hint = f"[COM ERROR] El puerto {self.puerto} está ocupado por Thonny IDE. Cierra Thonny o detén la ejecución."
                else:
                    err_hint = f"[COM ERROR] No se pudo abrir {self.puerto}: {se}"

                if self.callback_log:
                    self.callback_log(err_hint)

                # Intentar rescate si el puerto dio error (ej. Bluetooth o puerto erróneo)
                ok_res, p_res = self.autodetectar_puerto_esp32(puerto_excluir=self.puerto)
                if ok_res:
                    try:
                        self.serial_conn = serial.Serial(p_res, self.baudrate, timeout=1.5)
                        self.puerto = p_res
                        self.conectado = True
                        if self.callback_log:
                            self.callback_log(f"[COM RESCATE] ¡Conectado exitosamente en puerto rescatado {p_res}!")
                        return True, p_res
                    except Exception:
                        pass

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
                    self.callback_log(f"TX -> {repr(cmd_bytes)}")
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
                    self.callback_log(f"TX -> {repr(cmd_bytes)}")
                self.serial_conn.write(cmd_bytes)
                self.serial_conn.flush()

                inicio = time.time()
                while time.time() - inicio < 6:
                    if self.serial_conn.in_waiting > 0:
                        raw_line = self.serial_conn.readline()
                        linea = raw_line.decode('utf-8', errors='ignore').strip()
                        if self.callback_log and raw_line:
                            self.callback_log(f"RX <- {repr(raw_line)} -> '{linea}'")
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
                    self.callback_log(f"TX -> {repr(cmd_bytes)}")
                self.serial_conn.write(cmd_bytes)
                self.serial_conn.flush()

                inicio = time.time()
                while time.time() - inicio < 5:
                    if self.serial_conn.in_waiting > 0:
                        raw_line = self.serial_conn.readline()
                        linea = raw_line.decode('utf-8', errors='ignore').strip()
                        if self.callback_log and raw_line:
                            self.callback_log(f"RX <- {repr(raw_line)} -> '{linea}'")
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
                    self.callback_log(f"TX -> {repr(cmd_bytes)}")
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
                            self.callback_log(f"RX <- {repr(raw_line)} -> '{linea}'")
                        if "AUDIO_PLAY_READY" in linea:
                            ready = True
                            break
                    time.sleep(0.05)

                if not ready:
                    return False, "TIMEOUT AUDIO_PLAY_READY"

                import base64
                # Transmisión fluida Base64 en bloques de 1024 bytes (32ms por bloque)
                chunk_size = 1024
                for idx in range(0, len(pcm_bytes), chunk_size):
                    if self.cancelar_flag:
                        self.serial_conn.write(b"STOP\n")
                        self.serial_conn.flush()
                        return False, "CANCELADO"
                    chunk = pcm_bytes[idx : idx + chunk_size]
                    b64_str = base64.b64encode(chunk).decode('utf-8')
                    self.serial_conn.write(f"{b64_str}\n".encode('utf-8'))
                    self.serial_conn.flush()
                    time.sleep(0.002)

                self.serial_conn.write(b"AUDIO_PLAY_END\n")
                self.serial_conn.flush()

                # Esperar AUDIO_PLAY_OK — timeout = tamaño del audio + 5 segundos de margen (16000 Hz 16-bit mono = 32000 bytes/sec)
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
                            self.callback_log(f"RX <- {repr(raw_line)} -> '{linea}'")
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
                    self.callback_log(f"TX -> {repr(cmd_bytes)}")
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
                            self.callback_log(f"RX <- {repr(raw_line)} -> '{linea}'")
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
