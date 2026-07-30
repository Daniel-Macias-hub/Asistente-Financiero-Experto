"""
Módulo de Autodescubrimiento y Comunicación Serial/HTTP para ESP32-CAM.
Permite obtener la dirección IP asignada a la cámara automáticamente por Serial (COM14),
enviar credenciales Wi-Fi (SSID/Password) vía Serial, y verificar su estado de conexión HTTP.
"""
import time
import requests
import serial
import serial.tools.list_ports

def es_puerto_bluetooth_cam(p_info):
    """Devuelve True si el puerto es un enlace serie por Bluetooth."""
    desc = (p_info.description or "").lower()
    hwid = (p_info.hwid or "").lower()
    return any(k in desc or k in hwid for k in ["bluetooth", "bthenum", "vínculo bluetooth", "vinculo bluetooth", "serie estándar sobre"])

def enviar_configuracion_wifi_serial(ssid, password, puerto=None, puerto_excluir=None, timeout=14.0):
    """
    Envía credenciales Wi-Fi (SSID y Password) a la ESP32-CAM por el puerto serie indicado (SET_WIFI:ssid:pass).
    Espera a que el dispositivo guarde en NVS, se reinicie y reporte la IP obtenida por Wi-Fi.
    
    Returns:
        tuple (bool_exito, str_mensaje_o_ip)
    """
    if not ssid:
        return False, "SSID no puede estar vacío"

    # Cerrar cualquier gestor serial activo antes de reprogramar para evitar PermissionError
    try:
        camara_serial_mgr.cerrar()
    except Exception:
        pass

    # Advertencia anticipada si la red es 5G
    es_5g = any(tag in ssid.upper() for tag in ["5G", "5GHZ", "-5G", "_5G"])

    puertos_a_probar = []
    if puerto and puerto != puerto_excluir:
        puertos_a_probar.append(puerto)
    
    # Obtener puertos COM excluyendo el del S3 y los puertos Bluetooth
    for p_info in serial.tools.list_ports.comports():
        if p_info.device == puerto_excluir or es_puerto_bluetooth_cam(p_info):
            continue
        if p_info.device not in puertos_a_probar:
            puertos_a_probar.append(p_info.device)

    if not puertos_a_probar:
        return False, "No se encontraron puertos USB serie para la cámara"

    ultimo_err = "No se pudo conectar a la cámara por Serial"
    for p_try in puertos_a_probar:
        try:
            s = serial.Serial(p_try, 115200, timeout=1.5)
            s.dtr = False
            s.rts = False
            time.sleep(0.6)
            s.reset_input_buffer()
            s.reset_output_buffer()

            cmd = f"SET_WIFI:{ssid.strip()}:{password.strip()}\n"
            cmd_bytes = cmd.encode('utf-8')

            ok_recibido = False
            ip_hallada = None
            ap_fallback = False

            # Enviar continuamente comando SET_WIFI hasta que la cámara responda SET_WIFI_OK o la IP
            t0 = time.time()
            t_last_send = 0
            while time.time() - t0 < timeout:
                if not ok_recibido and (time.time() - t_last_send > 0.4):
                    try:
                        s.write(cmd_bytes)
                        s.flush()
                    except Exception:
                        pass
                    t_last_send = time.time()

                if s.in_waiting > 0:
                    linea = s.readline().decode('utf-8', errors='ignore').strip()
                    if "SET_WIFI_OK" in linea:
                        ok_recibido = True
                    if "CAM_IP:http://" in linea and "192.168.4.1" not in linea:
                        ip_hallada = linea.split("CAM_IP:")[1].strip()
                        break
                    elif "Servidor listo: http://" in linea:
                        ip_hallada = linea.split("Servidor listo: ")[1].strip()
                        break
                    elif "CAM_IP:AP_MODE" in linea or "192.168.4.1" in linea or "No se pudo conectar" in linea:
                        ap_fallback = True
                        break
                time.sleep(0.04)

            s.close()

            if ip_hallada:
                return True, ip_hallada
            elif ap_fallback or (ok_recibido and es_5g):
                err_msg = f"No se pudo conectar a '{ssid}'. Nota: La ESP32-CAM requiere Wi-Fi 2.4 GHz (las redes 5G no son compatibles)."
                return False, err_msg
            elif ok_recibido:
                return True, f"Configuración guardada en {p_try}. La cámara se está reiniciando..."

        except serial.SerialException as se:
            msg_str = str(se)
            if "PermissionError" in msg_str or "Access is denied" in msg_str or "Acceso denegado" in msg_str or "13" in msg_str:
                ultimo_err = f"El puerto {p_try} está ocupado por otro programa (ej: Thonny IDE, Monitor Serie o Vista Previa). Cierra Thonny para continuar."
            else:
                ultimo_err = f"Error en puerto {p_try}: {se}"
        except Exception as e:
            ultimo_err = f"Error en puerto {p_try}: {e}"

    return False, ultimo_err

def obtener_ip_camara_por_serial(puerto="COM14", timeout=2.5):
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
                if "CAM_IP:http://" in linea and "192.168.4.1" not in linea:
                    ip_hallada = linea.split("CAM_IP:")[1].strip()
                    break
                elif "Servidor listo: http://" in linea:
                    ip_hallada = linea.split("Servidor listo: ")[1].strip()
                    break
                elif ("http://172." in linea or "http://192." in linea or "http://10." in linea) and "192.168.4.1" not in linea:
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
    Escanea todos los puertos COM disponibles (excluyendo el del ESP32-S3 y Bluetooth)
    para localizar automáticamente la IP de la ESP32-CAM.
    
    Returns:
        tuple (ip_url, puerto_camara) o (None, None)
    """
    puertos_cand = serial.tools.list_ports.comports()
    disponibles = [p.device for p in puertos_cand if p.device != puerto_s3 and not es_puerto_bluetooth_cam(p)]

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
