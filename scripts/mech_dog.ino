#include <mech-dog-FOMO_inferencing.h>
#include "esp_camera.h"
#include <WiFi.h>
#include <WiFiUdp.h>

// ─── CONFIGURACIÓN WiFi ───────────────────────────────────────────
const char* WIFI_SSID = "Mandra";
const char* WIFI_PASS = "12345678";
const char* LAPTOP_IP = "10.182.136.52"; //aqui se pone la ip de tu computadora
const int   LAPTOP_PORT = 5005;

WiFiUDP udp;

// ─── PINES ESP32-S3 ───────────────────────────────────────────────
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

#define LED_PIN       2
#define CONFIANZA_MIN 0.6

const bool ES_RIESGO[] = {
    false, false, false,
    true,  false, true, true
};

#define FRAME_BYTES (EI_CLASSIFIER_INPUT_WIDTH * EI_CLASSIFIER_INPUT_HEIGHT)
static uint8_t frame_buf[FRAME_BYTES];

void enviar(const char* msg) {
    Serial.println(msg);
    if (WiFi.status() == WL_CONNECTED) {
        udp.beginPacket(LAPTOP_IP, LAPTOP_PORT);
        udp.print(msg);
        udp.endPacket();
    }
}

static int get_signal_data(size_t offset, size_t length, float *out_ptr) {
    for (size_t i = 0; i < length; i++) {
        uint8_t px = frame_buf[offset + i];
        out_ptr[i] = (float)((px << 16) | (px << 8) | px);
    }
    return 0;
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    pinMode(LED_PIN, OUTPUT);

    // ── Conectar WiFi ─────────────────────────────────────────────
    Serial.printf("Conectando a %s...\n", WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASS);

    int intentos = 0;
    while (WiFi.status() != WL_CONNECTED && intentos < 20) {
        delay(500);
        Serial.print(".");
        intentos++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("\n✅ WiFi OK — IP del ESP32: %s\n",
            WiFi.localIP().toString().c_str());
        udp.begin(4210);
    } else {
        Serial.println("\n⚠ Sin WiFi — solo Serial USB");
    }

    // ── Inicializar cámara ────────────────────────────────────────
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
        char msg[50];
        snprintf(msg, sizeof(msg), "Error camara: 0x%x", err);
        enviar(msg);
        while (true);
    }

    enviar("Camara OK");
    enviar("Iniciando deteccion...");
}

void loop() {

    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
        enviar("Fallo captura");
        delay(500);
        return;
    }

    if (fb->len != FRAME_BYTES) {
        char msg[50];
        snprintf(msg, sizeof(msg), "Tamano incorrecto: %d", (int)fb->len);
        enviar(msg);
        esp_camera_fb_return(fb);
        delay(500);
        return;
    }

    memcpy(frame_buf, fb->buf, FRAME_BYTES);
    esp_camera_fb_return(fb);

    signal_t signal;
    signal.total_length = FRAME_BYTES;
    signal.get_data     = &get_signal_data;

    ei_impulse_result_t result = {0};
    EI_IMPULSE_ERROR ei_err = run_classifier(&signal, &result, false);

    if (ei_err != EI_IMPULSE_OK) {
        char msg[50];
        snprintf(msg, sizeof(msg), "Error clasificador: %d", (int)ei_err);
        enviar(msg);
        delay(500);
        return;
    }

    bool hay_riesgo    = false;
    int  n_detecciones = 0;

    enviar("─────────────────────────────");

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

        char msg[80];
        snprintf(msg, sizeof(msg), "%s %s  conf:%.2f  pos:(%d,%d)",
            es_riesgo ? "ALERTA" : "OK",
            bb.label, bb.value, bb.x, bb.y);
        enviar(msg);
    }

    if (n_detecciones == 0) {
        enviar("Sin detecciones");
    }

    if (hay_riesgo) {
        enviar("!!! RIESGO DETECTADO !!!");
        for (int i = 0; i < 5; i++) {
            digitalWrite(LED_PIN, HIGH); delay(100);
            digitalWrite(LED_PIN, LOW);  delay(100);
        }
        delay(3000);
    } else {
        digitalWrite(LED_PIN, LOW);
    }

    char tiempo[50];
    snprintf(tiempo, sizeof(tiempo), "Tiempo: %llu ms",
        result.timing.dsp + result.timing.classification);
    enviar(tiempo);

    delay(500);
}