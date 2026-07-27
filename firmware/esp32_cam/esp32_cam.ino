/*
 * FIRMWARE ESP32-CAM (AI-Thinker OV2640)
 * CONTROL MANUAL DE FLASH LED MULTISOCKET (/led?state=1/0 & /stream?flash=1/0)
 * STREAM MJPEG Y FOTO CON ILUMINACIÓN FIJA SÓLIDA SIN PARPADEO
 */
#include "esp_camera.h"
#include <WiFi.h>
#include "esp_http_server.h"

// Credenciales WiFi
const char* ssid = "Router HUAWEI";
const char* password = "3C0461FB9BAD";

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
bool flash_led_encendido = false; // Por defecto APAGADO para evitar parpadeos

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
    
    // Vaciar el fotograma previo almacenado en el búfer de cola antes de la captura fresca
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

    res = httpd_resp_send(req, (const char *)fb->buf, fb->len);
    esp_camera_fb_return(fb);
    return res;
}

// Stream MJPEG continuo a alta velocidad sin parpadeo de LED
static esp_err_t stream_handler(httpd_req_t *req) {
    camera_fb_t * fb = NULL;
    esp_err_t res = ESP_OK;
    char * part_buf[64];

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
        vTaskDelay(10 / portTICK_PERIOD_MS); // Liberar tiempo de CPU a la pila WiFi
    }
    return res;
}

void startCameraServer() {
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.server_port = 80;
    config.max_open_sockets = 7;
    config.lru_purge_enable = true;

    httpd_uri_t capture_uri = {
        .uri       = "/capture",
        .method    = HTTP_GET,
        .handler   = capture_handler,
        .user_ctx  = NULL
    };

    httpd_uri_t stream_uri = {
        .uri       = "/stream",
        .method    = HTTP_GET,
        .handler   = stream_handler,
        .user_ctx  = NULL
    };

    httpd_uri_t led_uri = {
        .uri       = "/led",
        .method    = HTTP_GET,
        .handler   = led_handler,
        .user_ctx  = NULL
    };

    if (httpd_start(&stream_httpd, &config) == ESP_OK) {
        httpd_register_uri_handler(stream_httpd, &capture_uri);
        httpd_register_uri_handler(stream_httpd, &stream_uri);
        httpd_register_uri_handler(stream_httpd, &led_uri);
    }
}

void setup() {
    Serial.begin(115200);
    pinMode(FLASH_GPIO_NUM, OUTPUT);
    digitalWrite(FLASH_GPIO_NUM, LOW);

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

    // Configuración para Máxima Velocidad sin calentamiento ni parpadeo
    config.frame_size = FRAMESIZE_CIF;  // 400x296 (Ultrarrápido)
    config.jpeg_quality = 10;            // Compresión rápida
    config.fb_count = 2;                 // Búfer doble DMA para >25 FPS continuos

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("Error al iniciar camara: 0x%x", err);
        return;
    }

    sensor_t * s = esp_camera_sensor_get();
    if (s) {
        s->set_vflip(s, 1);   // Giro vertical
        s->set_hmirror(s, 1); // Espejo horizontal
    }

    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi Conectado!");
    Serial.print("Servidor listo: http://");
    Serial.println(WiFi.localIP());

    startCameraServer();
}

void loop() {
    delay(1000);
}
