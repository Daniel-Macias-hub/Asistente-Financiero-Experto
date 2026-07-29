/*
 * FIRMWARE ESP32-CAM (AI-Thinker OV2640)
 * CONFIGURACIÓN AUTOMÁTICA DE WI-FI (NVS + PORTAL CAUTIVO AP + APROVISIONAMIENTO SERIAL)
 * CONTROL MANUAL DE FLASH LED MULTISOCKET (/led?state=1/0 & /stream?flash=1/0)
 * STREAM MJPEG Y FOTO CON ILUMINACIÓN FIJA SÓLIDA SIN PARPADEO
 */
#include "esp_camera.h"
#include <WiFi.h>
#include <Preferences.h>
#include <DNSServer.h>
#include "esp_http_server.h"

// Definición de pines AI-THINKER ESP32-CAM
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22
#define FLASH_GPIO_NUM     4

#define PART_BOUNDARY "123456789000000000000987654321"
static const char* _STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char* _STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
static const char* _STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

httpd_handle_t stream_httpd = NULL;
bool flash_led_encendido = false;
Preferences preferences;

String wifi_ssid = "";
String wifi_pass = "";
bool ap_mode_active = false;
DNSServer dnsServer;

// ── HTML del Portal Cautivo para Configuración Wi-Fi en AP Mode ──────────────
const char PORTAL_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ESP32-CAM Wi-Fi Setup</title>
  <style>
    body { font-family: 'Segoe UI', Arial, sans-serif; background: #080C12; color: #E8F4FD; text-align: center; padding: 20px; }
    .card { background: #0F1923; max-width: 380px; margin: 20px auto; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); border: 1px solid #1E3A5F; }
    h2 { color: #00E676; margin-bottom: 20px; }
    input[type=text], input[type=password] { width: 90%; padding: 12px; margin: 10px 0; border: 1px solid #1A2740; background: #1A2740; color: #fff; border-radius: 6px; font-size: 14px; }
    input[type=submit] { background: #00E676; color: #000; font-weight: bold; border: none; padding: 12px 25px; border-radius: 6px; cursor: pointer; font-size: 15px; width: 95%; margin-top: 15px; }
    input[type=submit]:hover { background: #00C853; }
    .footer { margin-top: 15px; font-size: 12px; color: #6B7F95; }
  </style>
</head>
<body>
  <div class="card">
    <h2>📷 ESP32-CAM Wi-Fi</h2>
    <form action="/save" method="POST">
      <input type="text" name="ssid" placeholder="Nombre de Red Wi-Fi (SSID)" required><br>
      <input type="password" name="pass" placeholder="Contraseña WPA2" required><br>
      <input type="submit" value="Guardar y Conectar">
    </form>
    <div class="footer">Asistente Financiero Experto</div>
  </div>
</body>
</html>
)rawliteral";

// Control de Estado del LED Flash
static esp_err_t led_handler(httpd_req_t *req) {
    char buf[32];
    if (httpd_req_get_url_query_str(req, buf, sizeof(buf)) == ESP_OK) {
        char param[16];
        if (httpd_query_key_value(buf, "state", param, sizeof(param)) == ESP_OK) {
            int state = atoi(param);
            flash_led_encendido = (state == 1);
            digitalWrite(FLASH_GPIO_NUM, flash_led_encendido ? HIGH : LOW);
        }
    }
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    return httpd_resp_send(req, flash_led_encendido ? "LED ON" : "LED OFF", HTTPD_RESP_USE_STRLEN);
}

// Captura individual de fotografía JPEG
static esp_err_t capture_handler(httpd_req_t *req) {
    camera_fb_t * fb = NULL;
    esp_err_t res = ESP_OK;

    digitalWrite(FLASH_GPIO_NUM, flash_led_encendido ? HIGH : LOW);
    
    camera_fb_t * fb_old = esp_camera_fb_get();
    if (fb_old) {
        esp_camera_fb_return(fb_old);
    }

    fb = esp_camera_fb_get();

    if (!fb) {
        httpd_resp_send_500(req);
        return ESP_FAIL;
    }

    httpd_resp_set_type(req, "image/jpeg");
    httpd_resp_set_hdr(req, "Content-Disposition", "inline; filename=capture.jpg");
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    httpd_resp_set_hdr(req, "Connection", "close");

    res = httpd_resp_send(req, (const char *)fb->buf, fb->len);
    esp_camera_fb_return(fb);
    return res;
}

// Stream MJPEG continuo a alta velocidad
static esp_err_t stream_handler(httpd_req_t *req) {
    camera_fb_t * fb = NULL;
    esp_err_t res = ESP_OK;
    char part_buf[64];

    char q_buf[32];
    if (httpd_req_get_url_query_str(req, q_buf, sizeof(q_buf)) == ESP_OK) {
        char param[16];
        if (httpd_query_key_value(q_buf, "flash", param, sizeof(param)) == ESP_OK) {
            flash_led_encendido = (atoi(param) == 1);
        }
    }

    res = httpd_resp_set_type(req, _STREAM_CONTENT_TYPE);
    if (res != ESP_OK) return res;

    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");

    while (true) {
        digitalWrite(FLASH_GPIO_NUM, flash_led_encendido ? HIGH : LOW);
        fb = esp_camera_fb_get();
        if (!fb) {
            res = ESP_FAIL;
        } else {
            size_t hlen = snprintf((char *)part_buf, 64, _STREAM_PART, fb->len);
            res = httpd_resp_send_chunk(req, (const char *)part_buf, hlen);
            if (res == ESP_OK) {
                res = httpd_resp_send_chunk(req, (const char *)fb->buf, fb->len);
            }
            if (res == ESP_OK) {
                res = httpd_resp_send_chunk(req, _STREAM_BOUNDARY, strlen(_STREAM_BOUNDARY));
            }
            esp_camera_fb_return(fb);
        }
        if (res != ESP_OK) break;
        vTaskDelay(10 / portTICK_PERIOD_MS);
    }
    return res;
}

// Portal Cautivo HTTP Handler (AP Mode)
static esp_err_t portal_handler(httpd_req_t *req) {
    httpd_resp_set_type(req, "text/html");
    return httpd_resp_send(req, PORTAL_HTML, HTTPD_RESP_USE_STRLEN);
}

// Guardar credenciales enviadas por formulario Web en Portal Cautivo
static esp_err_t portal_save_handler(httpd_req_t *req) {
    char buf[128];
    int ret = httpd_req_recv(req, buf, sizeof(buf) - 1);
    if (ret > 0) {
        buf[ret] = '\0';
        char new_s[64] = {0};
        char new_p[64] = {0};
        httpd_query_key_value(buf, "ssid", new_s, sizeof(new_s));
        httpd_query_key_value(buf, "pass", new_p, sizeof(new_p));

        if (strlen(new_s) > 0) {
            preferences.begin("cam_wifi", false);
            preferences.putString("ssid", new_s);
            preferences.putString("pass", new_p);
            preferences.end();

            httpd_resp_send(req, "<h3>✅ Credenciales guardadas. Reiniciando camara...</h3>", HTTPD_RESP_USE_STRLEN);
            delay(1500);
            ESP.restart();
            return ESP_OK;
        }
    }
    httpd_resp_send_500(req);
    return ESP_FAIL;
}

void startCameraServer() {
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.server_port = 80;
    config.max_open_sockets = 4;
    config.lru_purge_enable = true;

    httpd_uri_t capture_uri = { .uri = "/capture", .method = HTTP_GET, .handler = capture_handler, .user_ctx = NULL };
    httpd_uri_t stream_uri  = { .uri = "/stream",  .method = HTTP_GET, .handler = stream_handler,  .user_ctx = NULL };
    httpd_uri_t led_uri     = { .uri = "/led",     .method = HTTP_GET, .handler = led_handler,     .user_ctx = NULL };
    httpd_uri_t portal_uri  = { .uri = "/",        .method = HTTP_GET, .handler = portal_handler,  .user_ctx = NULL };
    httpd_uri_t save_uri    = { .uri = "/save",    .method = HTTP_POST,.handler = portal_save_handler, .user_ctx = NULL };

    if (httpd_start(&stream_httpd, &config) == ESP_OK) {
        httpd_register_uri_handler(stream_httpd, &capture_uri);
        httpd_register_uri_handler(stream_httpd, &stream_uri);
        httpd_register_uri_handler(stream_httpd, &led_uri);
        httpd_register_uri_handler(stream_httpd, &portal_uri);
        httpd_register_uri_handler(stream_httpd, &save_uri);
    }
}

void iniciar_ap_mode() {
    ap_mode_active = true;
    Serial.println("\n⚠️ Entrando en MODO ACCESS POINT (AP) + PORTAL CAUTIVO...");
    WiFi.mode(WIFI_AP);
    WiFi.softAP("ESP32-CAM-AP");
    IPAddress apIP = WiFi.softAPIP();
    Serial.print("Servidor AP Activo: http://");
    Serial.println(apIP);
    Serial.println("CAM_IP:AP_MODE:http://192.168.4.1");

    dnsServer.start(53, "*", apIP);
    startCameraServer();
}

void guardar_y_conectar_wifi(String s, String p) {
    preferences.begin("cam_wifi", false);
    preferences.putString("ssid", s);
    preferences.putString("pass", p);
    preferences.end();
    Serial.println("✅ Credenciales Wi-Fi guardadas en NVS Flash.");
    Serial.println("SET_WIFI_OK");
    delay(500);
    ESP.restart();
}

void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.println("\n--- INICIANDO ESP32-CAM (Auto-WiFi NVS) ---");

    pinMode(FLASH_GPIO_NUM, OUTPUT);
    digitalWrite(FLASH_GPIO_NUM, LOW);

    if (PWDN_GPIO_NUM != -1) {
        pinMode(PWDN_GPIO_NUM, OUTPUT);
        digitalWrite(PWDN_GPIO_NUM, HIGH);
        delay(20);
        digitalWrite(PWDN_GPIO_NUM, LOW);
        delay(20);
    }

    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = Y2_GPIO_NUM;
    config.pin_d1 = Y3_GPIO_NUM;
    config.pin_d2 = Y4_GPIO_NUM;
    config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM;
    config.pin_d5 = Y7_GPIO_NUM;
    config.pin_d6 = Y8_GPIO_NUM;
    config.pin_d7 = Y9_GPIO_NUM;
    config.pin_xclk = XCLK_GPIO_NUM;
    config.pin_pclk = PCLK_GPIO_NUM;
    config.pin_vsync = VSYNC_GPIO_NUM;
    config.pin_href = HREF_GPIO_NUM;
    config.pin_sscb_sda = SIOD_GPIO_NUM;
    config.pin_sscb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn = PWDN_GPIO_NUM;
    config.pin_reset = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;
    config.frame_size = FRAMESIZE_CIF;  // 400x296
    config.jpeg_quality = 10;
    config.fb_count = 2;

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("Aviso 20MHz fail: 0x%x. Reintentando a 10MHz...\n", err);
        config.xclk_freq_hz = 10000000;
        err = esp_camera_init(&config);
    }

    if (err != ESP_OK) {
        Serial.printf("Error final al iniciar camara: 0x%x\n", err);
    } else {
        sensor_t * s = esp_camera_sensor_get();
        if (s) {
            s->set_vflip(s, 1);
            s->set_hmirror(s, 1);
        }
        Serial.println("Sensor de Cámara iniciado OK!");
    }

    // Cargar credenciales Wi-Fi desde memoria NVS
    preferences.begin("cam_wifi", true);
    wifi_ssid = preferences.getString("ssid", "");
    wifi_pass = preferences.getString("pass", "");
    preferences.end();

    if (wifi_ssid.length() > 0) {
        Serial.printf("Intentando conectar a Wi-Fi NVS '%s'...\n", wifi_ssid.c_str());
        WiFi.mode(WIFI_STA);
        WiFi.begin(wifi_ssid.c_str(), wifi_pass.c_str());
        int retries = 0;
        while (WiFi.status() != WL_CONNECTED && retries < 20) {
            delay(500);
            Serial.print(".");
            retries++;
        }
        if (WiFi.status() == WL_CONNECTED) {
            Serial.println("\n✅ Wi-Fi Conectado!");
            Serial.print("Servidor listo: http://");
            Serial.println(WiFi.localIP());
            Serial.print("CAM_IP:http://");
            Serial.println(WiFi.localIP());
            startCameraServer();
        } else {
            Serial.println("\n❌ No se pudo conectar a la Wi-Fi NVS.");
            iniciar_ap_mode();
        }
    } else {
        Serial.println("\n⚠️ Sin credenciales Wi-Fi NVS configuradas.");
        iniciar_ap_mode();
    }
}

void send_serial_frame() {
    digitalWrite(FLASH_GPIO_NUM, flash_led_encendido ? HIGH : LOW);
    camera_fb_t * fb_old = esp_camera_fb_get();
    if (fb_old) esp_camera_fb_return(fb_old);

    camera_fb_t * fb = esp_camera_fb_get();
    if (!fb) {
        Serial.println("FRAME_ERR");
        return;
    }
    Serial.printf("\n---FRAME_START---:%u\n", (unsigned int)fb->len);
    Serial.write(fb->buf, fb->len);
    Serial.println("\n---FRAME_END---");
    esp_camera_fb_return(fb);
}

void loop() {
    if (ap_mode_active) {
        dnsServer.processNextRequest();
    }

    if (Serial.available() > 0) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();
        if (cmd == "GET_IP" || cmd == "PING" || cmd == "CAM_IP" || cmd == "IP") {
            if (WiFi.status() == WL_CONNECTED) {
                Serial.print("CAM_IP:http://");
                Serial.println(WiFi.localIP());
            } else if (ap_mode_active) {
                Serial.println("CAM_IP:AP_MODE:http://192.168.4.1");
            } else {
                Serial.println("CAM_IP:DISCONNECTED");
            }
        } else if (cmd.startsWith("SET_WIFI:")) {
            // Sintaxis: SET_WIFI:nombre_red:password_red
            int idx1 = cmd.indexOf(':');
            int idx2 = cmd.indexOf(':', idx1 + 1);
            if (idx1 != -1 && idx2 != -1) {
                String new_s = cmd.substring(idx1 + 1, idx2);
                String new_p = cmd.substring(idx2 + 1);
                guardar_y_conectar_wifi(new_s, new_p);
            }
        } else if (cmd == "GET_FRAME" || cmd == "FRAME" || cmd == "SHOT") {
            send_serial_frame();
        } else if (cmd == "LED_ON") {
            flash_led_encendido = true;
            digitalWrite(FLASH_GPIO_NUM, HIGH);
            Serial.println("LED_ON_OK");
        } else if (cmd == "LED_OFF") {
            flash_led_encendido = false;
            digitalWrite(FLASH_GPIO_NUM, LOW);
            Serial.println("LED_OFF_OK");
        }
    }
    delay(20);
}
