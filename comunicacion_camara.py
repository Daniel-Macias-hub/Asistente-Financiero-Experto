"""
Módulo de Autodescubrimiento y Comunicación Serial/HTTP para ESP32-CAM.
Permite obtener la dirección IP asignada a la cámara automáticamente por Serial (COM14),
enviar credenciales Wi-Fi (SSID/Password) vía Serial, y verificar su estado de conexión HTTP.
"""
import time
import requests
import serial
import serial.tools.list_ports

def enviar_configuracion_wifi_serial(ssid, password, puerto=None, puerto_excluir=None, timeout=6.0):
    """
    Envía credenciales Wi-Fi (SSID y Password) a la ESP32-CAM por el puerto serie indicado (SET_WIFI:ssid:pass).
    Si el puerto no es especificado o falla, escanea automáticamente todos los puertos serie disponibles (excluyendo el del ESP32-S3).
    
    Returns:
        tuple (bool_exito, str_mensaje_ip)
    """
    if not ssid:
        return False, "SSID no puede estar vacío"

    puertos_a_probar = []
    if puerto and puerto != puerto_excluir:
        puertos_a_probar.append(puerto)
    
    # Agregar los demás puertos COM disponibles a la lista de intentos
    puertos_sys = [p.device for p in serial.tools.list_ports.comports() if p.device != puerto_excluir]
    for p in puertos_sys:
        if p not in puertos_a_probar:
            puertos_a_probar.append(p)

    if not puertos_a_probar:
        return False, "No se encontraron puertos serie para la cámara"

    ultimo_err = "No se pudo conectar a la cámara por Serial"
    for p_try in puertos_a_probar:
        try:
            s = serial.Serial(p_try, 115200, timeout=2.0)
            s.dtr = False
            s.rts = False
            # Esperar a que la ESP32-CAM complete la secuencia de arranque tras abrir el puerto (1.5s)
            time.sleep(1.5)
            s.reset_input_buffer()
            s.reset_output_buffer()

            cmd = f"SET_WIFI:{ssid.strip()}:{password.strip()}\n"
            cmd_bytes = cmd.encode('utf-8')

            # Enviar comando en reintentos por si la placa recién terminó de arrancar
            ok_recibido = False
            ip_hallada = None
            inicio = time.time()

            for _attempt in range(3):
                s.write(cmd_bytes)
                s.flush()
                time.sleep(0.3)
                if s.in_waiting > 0:
                    break

            while time.time() - inicio < timeout:
                if s.in_waiting > 0:
                    linea = s.readline().decode('utf-8', errors='ignore').strip()
                    if "SET_WIFI_OK" in linea:
                        ok_recibido = True
                    if "CAM_IP:http://" in linea:
                        ip_hallada = linea.split("CAM_IP:")[1].strip()
                        break
                    elif "Servidor listo: http://" in linea:
                        ip_hallada = linea.split("Servidor listo: ")[1].strip()
                        break
                time.sleep(0.05)

            s.close()
            if ok_recibido or ip_hallada:
                return True, ip_hallada or f"Configuración enviada correctamente en {p_try}. Reiniciando cámara..."
        except Exception as e:
            ultimo_err = f"Error en puerto {p_try}: {e}"

    return False, ultimo_err

def obtener_ip_camara_por_serial(puerto="COM3", timeout=2.5):
    """
    Se conecta al puerto serie de la ESP32-CAM y le solicita su dirección IP.
    
    Returns:
        tuple (str_ip_url, str_puerto_usado) o (None, None)
    """
    try:
        s = serial.Serial(puerto, 115200, timeout=timeout)
        time.sleep(0.3)
        s.reset_input_buffer()
        s.reset_output_buffer()

        s.write(b"GET_IP\n")
        s.flush()

        inicio = time.time()
        ip_hallada = None

        while time.time() - inicio < timeout:
            if s.in_waiting > 0:
                linea = s.readline().decode('utf-8', errors='ignore').strip()
                if "CAM_IP:http://" in linea:
                    ip_hallada = linea.split("CAM_IP:")[1].strip()
                    break
                elif "Servidor listo: http://" in linea:
                    ip_hallada = linea.split("Servidor listo: ")[1].strip()
                    break
                elif "http://172." in linea or "http://192." in linea or "http://10." in linea or "http://192.168.4.1" in linea:
                    parts = linea.split("http://")
                    if len(parts) > 1:
                        ip_clean = parts[1].split()[0].split("/")[0]
                        ip_hallada = f"http://{ip_clean}"
                        break
            time.sleep(0.05)

        s.close()
        return ip_hallada, puerto
    except Exception as e:
        return None, None

def autodetectar_ip_camara(puerto_s3=None):
    """
    Escanea todos los puertos COM disponibles (excluyendo el del ESP32-S3 si fue indicado)
    para localizar automáticamente la IP de la ESP32-CAM.
    
    Returns:
        tuple (ip_url, puerto_camara) o (None, None)
    """
    puertos = serial.tools.list_ports.comports()
    disponibles = [p.device for p in puertos if p.device != puerto_s3]

    for port in disponibles:
        ip, p_ok = obtener_ip_camara_por_serial(port, timeout=1.8)
        if ip:
            return ip, p_ok

    return None, None

def probar_conexion_camara_http(url_base, timeout_sec=2.5):
    """
    Realiza una petición HTTP rápida a /capture para confirmar que el servidor web de la cámara responde.
    Fuerza cabecera Connection: close para evitar retención de sockets TCP.
    
    Returns:
        tuple (bool_exito, str_mensaje)
    """
    if not url_base:
        return False, "URL de Cámara Vacía"

    url_base = url_base.strip().rstrip("/")
    if not url_base.startswith("http://") and not url_base.startswith("https://"):
        url_base = f"http://{url_base}"

    capture_url = f"{url_base}/capture"
    try:
        headers = {'Connection': 'close'}
        r = requests.get(capture_url, headers=headers, timeout=timeout_sec)
        if r.status_code == 200 and len(r.content) > 100:
            return True, f"Conectado OK ({len(r.content)//1024} KB)"
        else:
            return False, f"Código HTTP {r.status_code}"
    except requests.exceptions.ConnectTimeout:
        return False, f"Timeout al conectar con {url_base}"
    except Exception as e:
        return False, f"Error: {e}"

class CamaraSerialManager:
    """Mantiene una conexión serial persistente con la ESP32-CAM para streaming sin abrir/cerrar puertos."""
    def __init__(self, puerto="COM14"):
        self.puerto = puerto
        self.conn = None

    def abrir(self, timeout=2.0):
        if self.conn and self.conn.is_open:
            return True
        try:
            self.conn = serial.Serial(self.puerto, 115200, timeout=timeout)
            time.sleep(0.15)
            self.conn.reset_input_buffer()
            return True
        except Exception as e:
            print(f"[SERIAL MANAGER ERR] No se pudo abrir {self.puerto}: {e}")
            self.conn = None
            return False

    def capturar_frame(self, timeout=2.0):
        if not self.conn or not self.conn.is_open:
            if not self.abrir(timeout):
                return None
        try:
            import cv2
            import numpy as np
            self.conn.reset_input_buffer()
            self.conn.write(b"GET_FRAME\n")
            self.conn.flush()

            inicio = time.time()
            len_frame = 0
            header_found = False

            while time.time() - inicio < timeout:
                if self.conn.in_waiting > 0:
                    linea = self.conn.readline().decode('utf-8', errors='ignore').strip()
                    if "---FRAME_START---:" in linea:
                        try:
                            len_frame = int(linea.split("---FRAME_START---:")[1])
                            header_found = True
                            break
                        except Exception:
                            pass
                time.sleep(0.01)

            if not header_found or len_frame == 0:
                return None

            img_bytes = self.conn.read(len_frame)
            if len(img_bytes) == len_frame:
                arr = np.frombuffer(img_bytes, dtype=np.uint8)
                img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                return img
            return None
        except Exception as e:
            print(f"[SERIAL CAPTURE ERR] {e}")
            self.cerrar()
            return None

    def cerrar(self):
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None

camara_serial_mgr = CamaraSerialManager("COM14")

def capturar_frame_por_serial(puerto="COM14", timeout=3.0):
    camara_serial_mgr.puerto = puerto
    return camara_serial_mgr.capturar_frame(timeout=timeout)
