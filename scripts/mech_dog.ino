#include <mech-dog-FOMO_inferencing.h>
#include "esp_camera.h"

// ─── PINES ESP32-S3 ───────────────────────────────────────────
#define PWDN_GPIO_NUM  -1
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM  15
#define SIOD_GPIO_NUM  4
#define SIOC_GPIO_NUM  5
#define Y9_GPIO_NUM    16
#define Y8_GPIO_NUM    17
#define Y7_GPIO_NUM    18
#define Y6_GPIO_NUM    12
#define Y5_GPIO_NUM    10
#define Y4_GPIO_NUM    8
#define Y3_GPIO_NUM    9
#define Y2_GPIO_NUM    11
#define VSYNC_GPIO_NUM 6
#define HREF_GPIO_NUM  7
#define PCLK_GPIO_NUM  13

#define LED_PIN        2
#define CONFIANZA_MIN  0.6

const bool ES_RIESGO[] = {
    false,  // 0: bolsa_ok
    false,  // 1: cables_ok
    false,  // 2: caja_ok
    true,   // 3: mesa_riesgo
    false,  // 4: mochila_ok
    true,   // 5: mochila_riesgo
    true    // 6: silla_riesgo
};

// Buffer estático — no usa heap dinámico
#define FRAME_BYTES (EI_CLASSIFIER_INPUT_WIDTH * EI_CLASSIFIER_INPUT_HEIGHT)
static uint8_t frame_buf[FRAME_BYTES];

// Callback correcto para FOMO con imagen grayscale
static int get_signal_data(size_t offset, size_t length, float *out_ptr) {
    for (size_t i = 0; i < length; i++) {
        uint8_t px  = frame_buf[offset + i];
        // FOMO necesita RGB empaquetado aunque sea gris
        out_ptr[i]  = (float)((px << 16) | (px << 8) | px);
    }
    return 0;
}

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n========================================");
    Serial.println("  MechDog — Detector FOMO");
    Serial.println("========================================\n");

    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);

    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer   = LEDC_TIMER_0;
    config.pin_d0       = Y2_GPIO_NUM;
    config.pin_d1       = Y3_GPIO_NUM;
    config.pin_d2       = Y4_GPIO_NUM;
    config.pin_d3       = Y5_GPIO_NUM;
    config.pin_d4       = Y6_GPIO_NUM;
    config.pin_d5       = Y7_GPIO_NUM;
    config.pin_d6       = Y8_GPIO_NUM;
    config.pin_d7       = Y9_GPIO_NUM;
    config.pin_xclk     = XCLK_GPIO_NUM;
    config.pin_pclk     = PCLK_GPIO_NUM;
    config.pin_vsync    = VSYNC_GPIO_NUM;
    config.pin_href     = HREF_GPIO_NUM;
    config.pin_sccb_sda = SIOD_GPIO_NUM;
    config.pin_sccb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn     = PWDN_GPIO_NUM;
    config.pin_reset    = RESET_GPIO_NUM;
    config.xclk_freq_hz = 8000000;
    config.pixel_format = PIXFORMAT_GRAYSCALE;
    config.frame_size   = FRAMESIZE_96X96;
    config.fb_count     = 1;
    config.fb_location  = CAMERA_FB_IN_PSRAM;
    config.grab_mode    = CAMERA_GRAB_WHEN_EMPTY;

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("❌ Error camara: 0x%x\n", err);
        while (true);
    }

    Serial.printf("✅ Camara OK — %dx%d\n",
        EI_CLASSIFIER_INPUT_WIDTH,
        EI_CLASSIFIER_INPUT_HEIGHT);
    Serial.printf("Buffer: %d bytes\n", FRAME_BYTES);
    Serial.println("\nClases:");
    for (int i = 0; i < EI_CLASSIFIER_LABEL_COUNT; i++) {
        Serial.printf("  [%d] %s %s\n", i,
            ei_classifier_inferencing_categories[i],
            ES_RIESGO[i] ? "<- RIESGO" : "");
    }
    Serial.println("\n> Iniciando...\n");
}

void loop() {

    // 1. Capturar
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
        Serial.println("❌ Fallo captura");
        delay(500);
        return;
    }

    if (fb->len != FRAME_BYTES) {
        Serial.printf("❌ Tamaño incorrecto: %d\n", fb->len);
        esp_camera_fb_return(fb);
        delay(500);
        return;
    }

    memcpy(frame_buf, fb->buf, FRAME_BYTES);
    esp_camera_fb_return(fb);   // liberar ANTES de inferencia

    // 2. Señal
    signal_t signal;
    signal.total_length = FRAME_BYTES;
    signal.get_data     = &get_signal_data;

    // 3. Inferencia
    ei_impulse_result_t result = {0};
    EI_IMPULSE_ERROR ei_err = run_classifier(&signal, &result, false);

    if (ei_err != EI_IMPULSE_OK) {
        Serial.printf("❌ Error clasificador: %d\n", ei_err);
        delay(500);
        return;
    }

    // 4. Resultados
    Serial.println("─────────────────────────────");

    bool hay_riesgo    = false;
    int  n_detecciones = 0;

    for (uint32_t i = 0; i < result.bounding_boxes_count; i++) {
        ei_impulse_result_bounding_box_t bb = result.bounding_boxes[i];

        if (bb.value < CONFIANZA_MIN) continue;
        n_detecciones++;

        bool es_riesgo = false;
        for (int j = 0; j < EI_CLASSIFIER_LABEL_COUNT; j++) {
            if (strcmp(bb.label,
                    ei_classifier_inferencing_categories[j]) == 0) {
                es_riesgo = ES_RIESGO[j];
                break;
            }
        }
        if (es_riesgo) hay_riesgo = true;

        Serial.printf("%s %s  conf:%.2f  pos:(%d,%d)\n",
            es_riesgo ? "ALERTA" : "OK",
            bb.label, bb.value, bb.x, bb.y);
    }

    if (n_detecciones == 0) {
        Serial.println("  Sin detecciones");
    }

    // 5. Alerta
    if (hay_riesgo) {
        Serial.println("\n!!! RIESGO DETECTADO !!!\n");
        for (int i = 0; i < 5; i++) {
            digitalWrite(LED_PIN, HIGH); delay(100);
            digitalWrite(LED_PIN, LOW);  delay(100);
        }
        delay(3000);
    } else {
        digitalWrite(LED_PIN, LOW);
    }

    Serial.printf("Tiempo: %llu ms\n",
        result.timing.dsp + result.timing.classification);

    delay(500);
}