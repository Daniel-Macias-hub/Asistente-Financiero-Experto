#include <Arduino.h>
#include "driver/i2s.h"
#include "mbedtls/base64.h"
#include <math.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ==============================================================================
// CONFIGURACIÓN DE PINES (ESP32-S3)
// ==============================================================================
// Bocina MAX98357A (TX)
#define I2S_SPK_NUM     I2S_NUM_1 
#define SPK_BCLK        15
#define SPK_WS          16
#define SPK_DIN         7

// Micrófono INMP441 (RX)
#define I2S_MIC_NUM     I2S_NUM_0
#define MIC_BCLK        5
#define MIC_WS          4
#define MIC_DOUT        6

// Pantalla OLED SSD1306
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define OLED_SDA 41
#define OLED_SCL 42

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

#define SAMPLE_RATE     16000
bool is_playing = false;

// Variables para animación idle
unsigned long last_blink = 0;
unsigned long last_text_change = 0;
bool show_jas = false;
String current_state = "IDLE";

// ------------------------------------------------------------------------------
// FUNCIONES GRÁFICAS (OLED)
// ------------------------------------------------------------------------------
void drawHappyFace(bool blink = false) {
  display.clearDisplay();
  
  // Ojos (Parpadeo)
  if (blink) {
    display.drawLine(35, 25, 45, 25, SSD1306_WHITE);
    display.drawLine(83, 25, 93, 25, SSD1306_WHITE);
  } else {
    display.fillCircle(40, 25, 5, SSD1306_WHITE);
    display.fillCircle(88, 25, 5, SSD1306_WHITE);
  }
  
  // Sonrisa
  for(int x = 40; x <= 88; x++) {
    int y = 45 + (int)(10.0 * sin(M_PI * (x - 40) / 48.0));
    display.drawPixel(x, y, SSD1306_WHITE);
    display.drawPixel(x, y+1, SSD1306_WHITE); 
  }

  // Texto
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  
  if (show_jas) {
    // Centrado para 3 letras
    display.setCursor(55, 0);
    display.print("JAS");
  } else {
    display.setCursor(30, 0);
    display.print("LISTO EN PC");
  }
  
  display.display();
}

void showMessage(String msg1, String msg2 = "") {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 20);
  display.println(msg1);
  if (msg2 != "") {
    display.setCursor(0, 40);
    display.println(msg2);
  }
  display.display();
}

// ------------------------------------------------------------------------------
// CONFIGURACIÓN INICIAL
// ------------------------------------------------------------------------------
void setup() {
  Serial.begin(921600);

  // Inicializar I2C para OLED
  Wire.begin(OLED_SDA, OLED_SCL);
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("OLED fallo."));
  }
  display.clearDisplay();
  showMessage("INICIANDO...");

  // Configuración de Bocina I2S (MAX98357A)
  i2s_config_t i2s_spk_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 1024,
    .use_apll = false,
    .tx_desc_auto_clear = true,
    .fixed_mclk = 0
  };
  i2s_pin_config_t pin_spk_config = {
    .mck_io_num = I2S_PIN_NO_CHANGE,
    .bck_io_num = SPK_BCLK,
    .ws_io_num = SPK_WS,
    .data_out_num = SPK_DIN,
    .data_in_num = I2S_PIN_NO_CHANGE
  };
  i2s_driver_install(I2S_SPK_NUM, &i2s_spk_config, 0, NULL);
  i2s_set_pin(I2S_SPK_NUM, &pin_spk_config);
  i2s_zero_dma_buffer(I2S_SPK_NUM);

  // Configuración de Micrófono I2S (INMP441)
  i2s_config_t i2s_mic_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT, // El INMP441 usa 24 bits en un slot de 32 bits
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 1024,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };
  i2s_pin_config_t pin_mic_config = {
    .mck_io_num = I2S_PIN_NO_CHANGE,
    .bck_io_num = MIC_BCLK,
    .ws_io_num = MIC_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = MIC_DOUT
  };
  i2s_driver_install(I2S_MIC_NUM, &i2s_mic_config, 0, NULL);
  i2s_set_pin(I2S_MIC_NUM, &pin_mic_config);

  Serial.setTimeout(100);
  drawHappyFace();
}

// ------------------------------------------------------------------------------
// BUCLE PRINCIPAL
// ------------------------------------------------------------------------------
void loop() {
  if (Serial.available() > 0) {
    String line = Serial.readStringUntil('\n');
    line.trim();

    if (line == "PING") {
      Serial.println("PONG");
    } 
    // Comandos de Interfaz Gráfica
    else if (line.startsWith("STATE:")) {
      String state = line.substring(6); 
      if (state.startsWith("ESCUCHANDO")) {
        showMessage("ESCUCHANDO...");
      } else if (state.startsWith("PROCESANDO")) {
        showMessage("PROCESANDO...");
      } else if (state.startsWith("IDLE")) {
        drawHappyFace();
      } else {
        showMessage(state);
      }
      current_state = state;
    }
    // Prueba Diagnóstica de OLED
    else if (line == "OLED_TEST" || line == "OLED_ANIM") {
      showMessage("TEST OLED", "FUNCIONANDO OK");
      delay(1500);
      Serial.println(line + "_OK");
      drawHappyFace();
      current_state = "IDLE";
    }
    // Prueba Diagnóstica de Audio (Melodía 4s + fade-out)
    else if (line == "AUDIO_TEST") {
      showMessage("TEST AUDIO", "MUSICA...");
      size_t bytes_written = 0;
      int16_t sample;
      
      // Notas musicales (Do, Mi, Sol, Do agudo, Sol, Mi)
      float melody[] = {261.63, 329.63, 392.00, 523.25, 392.00, 329.63}; 
      int num_notes = 6;
      const unsigned long DURATION_MS = 4000;  // 4s para dejar margen al timeout de Python (5s)
      const unsigned long FADEOUT_MS   = 500;   // Ultimo medio segundo se apaga suavemente

      unsigned long start_time = millis();
      long total_samples = 0;
      
      while (true) {
        unsigned long elapsed_ms = millis() - start_time;
        if (elapsed_ms >= DURATION_MS) break;

        int current_note_idx = (elapsed_ms / 300) % num_notes;
        float freq = melody[current_note_idx];
        
        // Calcular amplitud: fade-out suave en los ultimos FADEOUT_MS
        float amplitude = 8000.0;
        if (elapsed_ms > (DURATION_MS - FADEOUT_MS)) {
          float fade_ratio = 1.0 - (float)(elapsed_ms - (DURATION_MS - FADEOUT_MS)) / FADEOUT_MS;
          amplitude = 8000.0 * fade_ratio;
        }
        
        // Escribir en trozos para no bloquear el watchdog
        for (int i = 0; i < 200; i++) {
          sample = (int16_t)(amplitude * sin(2.0 * M_PI * freq * total_samples / SAMPLE_RATE));
          i2s_write(I2S_SPK_NUM, &sample, sizeof(sample), &bytes_written, portMAX_DELAY);
          total_samples++;
        }
      }
      i2s_zero_dma_buffer(I2S_SPK_NUM);
      delay(50); // Pequeño respiro antes de contestar
      Serial.println("AUDIO_TEST_OK");
      drawHappyFace();
      current_state = "IDLE";
    }
    // Prueba Diagnóstica del Micrófono (Graba 5s y reproduce al final)
    else if (line == "MIC_TEST") {
      // 1. Cuenta regresiva en OLED
      for (int i = 3; i > 0; i--) {
        showMessage("TEST MICROFONO", "Habla en " + String(i) + "...");
        delay(1000);
      }
      
      showMessage("GRABANDO...", "Di algo (5s)");
      
      // Reservar memoria para 5 segundos de audio (16kHz * 5s * 2 bytes = 160 KB)
      const int MAX_SAMPLES = 16000 * 5;
      int16_t *record_buffer = (int16_t *)malloc(MAX_SAMPLES * sizeof(int16_t));
      
      const int BLOCK_SIZE = 256; 
      int32_t mic_buf[BLOCK_SIZE];
      size_t bytes_read = 0;
      
      double total_sq = 0;
      int32_t min_v = 32767, max_v = -32768;
      int total_samples = 0;

      unsigned long start_time = millis();

      while (millis() - start_time < 5000 && total_samples < MAX_SAMPLES) {
        esp_err_t err = i2s_read(I2S_MIC_NUM, mic_buf, sizeof(mic_buf), &bytes_read, portMAX_DELAY);
        if (err != ESP_OK || bytes_read == 0) continue;

        int num_samples = bytes_read / sizeof(int32_t);
        for (int i = 0; i < num_samples && total_samples < MAX_SAMPLES; i++) {
          // El INMP441 envía audio de 24 bits alineado a la izquierda (MSB).
          // El shift correcto para convertir a 16-bits con ganancia natural es >> 14
          int32_t sample32 = mic_buf[i];
          sample32 >>= 14;
          
          // Evitar distorsión si hablamos muy fuerte cerca
          if (sample32 > 32767) sample32 = 32767;
          if (sample32 < -32768) sample32 = -32768;
          int16_t s16 = (int16_t)sample32;
          
          if (record_buffer) {
            record_buffer[total_samples] = s16;
          }
          
          if (s16 < min_v) min_v = s16;
          if (s16 > max_v) max_v = s16;
          total_sq += (double)s16 * s16;
          total_samples++;
        }
      }

      // 3. Calcular RMS y mandar reporte a Python primero
      double rms = 0;
      if (total_samples > 0) {
        rms = sqrt(total_sq / total_samples);
      }
      
      Serial.print("[STEP 5.1] Muestras_16=[], Min=");
      Serial.print(min_v);
      Serial.print(", Max=");
      Serial.print(max_v);
      Serial.print(", RMS=");
      Serial.println(rms, 2);
      Serial.println("MIC_TEST_OK");
      
      // 4. Reproducir el audio grabado
      if (record_buffer) {
        showMessage("REPRODUCIENDO...", "Escucha tu voz");
        size_t bw = 0;
        // Reproducimos en trozos pequeños para no bloquear el procesador
        for(int i = 0; i < total_samples; i += 1024) {
           int chunk_size = total_samples - i;
           if (chunk_size > 1024) chunk_size = 1024;
           i2s_write(I2S_SPK_NUM, &record_buffer[i], chunk_size * sizeof(int16_t), &bw, portMAX_DELAY);
        }
        i2s_zero_dma_buffer(I2S_SPK_NUM);
        free(record_buffer); // Liberar la memoria RAM
      }
      
      showMessage("TEST COMPLETADO", "RMS: " + String((int)rms));
      delay(2000);
      drawHappyFace();
      current_state = "IDLE";
    }
    // Captura silenciosa de voz para STT (PCM -> Base64 -> Serial, sin reproducción)
    else if (line.startsWith("MIC_CAPTURE:")) {
      int dur_sec = line.substring(12).toInt();
      if (dur_sec < 1 || dur_sec > 10) dur_sec = 4;

      showMessage("ESCUCHANDO...", "Habla ahora");

      int max_samples = 16000 * dur_sec;
      int16_t *cap_buf = (int16_t *)malloc(max_samples * sizeof(int16_t));
      if (!cap_buf) {
        Serial.println("MIC_CAPTURE_ERROR: sin memoria");
      } else {
        const int BLOCK_SIZE = 256;
        int32_t mic_buf[BLOCK_SIZE];
        size_t bytes_read = 0;
        int total_samples = 0;

        unsigned long start_time = millis();
        while ((int)(millis() - start_time) < dur_sec * 1000 && total_samples < max_samples) {
          i2s_read(I2S_MIC_NUM, mic_buf, sizeof(mic_buf), &bytes_read, portMAX_DELAY);
          int n = bytes_read / sizeof(int32_t);
          for (int i = 0; i < n && total_samples < max_samples; i++) {
            int32_t s = mic_buf[i] >> 14;
            if (s >  32767) s =  32767;
            if (s < -32768) s = -32768;
            cap_buf[total_samples++] = (int16_t)s;
          }
        }

        // Enviar PCM en bloques Base64
        // 256 muestras * 2 bytes = 512 bytes binarios → Base64 = ceil(512/3)*4 = 684 bytes (cabe en 700)
        Serial.println("MIC_CAPTURE_START");
        const int CHUNK_SAMPLES = 256;
        unsigned char b64_out[800];  // 700+ bytes es suficiente para 256 muestras
        for (int i = 0; i < total_samples; i += CHUNK_SAMPLES) {
          int n = total_samples - i;
          if (n > CHUNK_SAMPLES) n = CHUNK_SAMPLES;
          size_t out_len = 0;
          int ret = mbedtls_base64_encode(b64_out, sizeof(b64_out), &out_len,
                                (const unsigned char *)&cap_buf[i], n * sizeof(int16_t));
          if (ret == 0 && out_len > 0) {
            b64_out[out_len] = '\0';
            Serial.println((char*)b64_out);
            Serial.flush();  // Asegurar que el bloque llegue antes del siguiente
          }
        }
        free(cap_buf);
        Serial.println("MIC_CAPTURE_END");
        Serial.flush();
      }
      drawHappyFace();
      current_state = "IDLE";
    }
    // Reproducción de voz hablada por el asistente (Base64 -> PCM)
    else if (line.startsWith("AUDIO_PLAY:")) {
      showMessage("HABLANDO...");
      // Vaciar cualquier basura previa en el buffer serial
      while(Serial.available()) Serial.read();
      Serial.println("AUDIO_PLAY_READY");
      is_playing = true;
      
      while (is_playing) {
        if (Serial.available() > 0) {
          String b64_line = Serial.readStringUntil('\n');
          b64_line.trim();
          
          if (b64_line == "AUDIO_PLAY_END") {
            Serial.println("AUDIO_PLAY_OK");
            is_playing = false;
            i2s_zero_dma_buffer(I2S_SPK_NUM);
          }
          else if (b64_line == "STOP") {
            is_playing = false;
            i2s_zero_dma_buffer(I2S_SPK_NUM);
          }
          else if (b64_line.length() > 0) {
            size_t output_len = 0;
            unsigned char pcm_buffer[2048]; 
            
            int ret = mbedtls_base64_decode(
                pcm_buffer, sizeof(pcm_buffer), &output_len,
                (const unsigned char*)b64_line.c_str(), b64_line.length()
            );
            
            if (ret == 0 && output_len > 0) {
              size_t bytes_written = 0;
              i2s_write(I2S_SPK_NUM, pcm_buffer, output_len, &bytes_written, portMAX_DELAY);
            }
            // ACK: confirmar que el bloque fue procesado antes de recibir el siguiente
            Serial.println("K");
          }
        }
      }
      drawHappyFace();
      current_state = "IDLE";
    }
  } else {
    // Si no hay comandos nuevos y estamos en IDLE, la carita parpadea y alterna texto
    if (current_state.startsWith("IDLE") || current_state == "") {
      if (millis() - last_blink > 4000) {
        drawHappyFace(true);  // Cierra los ojos
        delay(150);
        drawHappyFace(false); // Abre los ojos
        last_blink = millis();
      }
      
      // Alternar texto cada 10 segundos
      if (millis() - last_text_change > 10000) {
        show_jas = !show_jas;
        drawHappyFace(false);
        last_text_change = millis();
      }
    }
  }
}
