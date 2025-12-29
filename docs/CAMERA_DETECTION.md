# Camera Detection and Integration Guide for ESP32

## Overview

Adding camera support to ZIAS enables face recognition as an optional authentication method alongside RFID, PIR, and BLE. The ESP32-CAM is the recommended hardware.

## Hardware Options

### Option 1: ESP32-CAM (Recommended)
- Built-in camera (OV2640)
- Cost: Rs. 400-600
- Suitable for face recognition
- Limited GPIO pins

### Option 2: ESP32 + External Camera
- ESP32 DevKit + OV2640/OV7670
- Cost: Rs. 600-800
- More GPIO available
- Complex wiring

## Camera Detection Code

### Auto-Detection Method

```cpp
#include <esp_camera.h>

bool hasCamera = false;

/**
 * Detect camera hardware
 * Tests camera initialization
 */
void detectCamera() {
    Serial.println("Detecting camera...");
    
    // Camera configuration for ESP32-CAM
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
    
    // Frame size for face detection
    config.frame_size = FRAMESIZE_QVGA;  // 320x240
    config.jpeg_quality = 12;
    config.fb_count = 1;
    
    // Try to initialize camera
    esp_err_t err = esp_camera_init(&config);
    
    if (err == ESP_OK) {
        hasCamera = true;
        Serial.println("[✓] Camera detected (OV2640)");
        
        // Test capture
        camera_fb_t *fb = esp_camera_fb_get();
        if (fb) {
            Serial.printf("    Resolution: %dx%d\n", fb->width, fb->height);
            esp_camera_fb_return(fb);
        }
    } else {
        hasCamera = false;
        Serial.println("[✗] Camera not found");
        Serial.printf("    Error: 0x%x\n", err);
    }
}
```

## Integration with Universal Node

Add to `esp32_universal.ino`:

```cpp
// In setup()
void setup() {
    // ... existing code ...
    
    // Detect camera (if supported)
    #ifdef CAMERA_MODEL_AI_THINKER
        detectCamera();
    #endif
    
    // ... rest of setup ...
}

// In loop()
void loop() {
    // ... existing code ...
    
    // Capture and process face if camera enabled
    if (hasCamera && hasPIR) {
        int pirState = digitalRead(PIR_SENSOR_PIN);
        if (pirState == HIGH) {
            captureFaceAndPublish();
        }
    }
}
```

## Face Detection Library

**Option 1: ESP-WHO (Espressif)**
```cpp
#include "esp_camera.h"
#include "fd_forward.h"  // Face detection
#include "fr_forward.h"  // Face recognition

void captureFaceAndPublish() {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
        return;
    }
    
    // Detect faces
    dl_matrix3du_t *image_matrix = dl_matrix3du_alloc(1, fb->width, fb->height, 3);
    fmt2rgb888(fb->buf, fb->len, fb->format, image_matrix->item);
    
    box_array_t *boxes = face_detect(image_matrix, &mtmn_config);
    
    if (boxes && boxes->len > 0) {
        Serial.println("Face detected!");
        
        // Get face ID and publish to MQTT
        // TODO: Face recognition logic
        
        publishFaceEvent("face_detected", boxes->len);
    }
    
    dl_matrix3du_free(image_matrix);
    esp_camera_fb_return(fb);
}
```

**Option 2: Cloud API (easier, requires internet)**
```cpp
void captureFaceAndPublish() {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) return;
    
    // Send image to cloud API for face recognition
    HTTPClient http;
    http.begin(FACE_API_URL);
    http.addHeader("Content-Type", "image/jpeg");
    
    int httpCode = http.POST(fb->buf, fb->len);
    
    if (httpCode == 200) {
        String response = http.getString();
        // Parse face ID from response
        publishFaceEvent("recognized", response);
    }
    
    http.end();
    esp_camera_fb_return(fb);
}
```

## Pin Definitions for ESP32-CAM

```cpp
// config.h additions for ESP32-CAM
#define CAMERA_MODEL_AI_THINKER

// Camera pins (AI-Thinker ESP32-CAM)
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

// Note: Limited GPIO available on ESP32-CAM
// PIR can use GPIO 13 or 12
// RFID not recommended (pins conflict)
```

## Deployment Strategies

### Strategy 1: ESP32-CAM at Entry (Face Only)
```
[Entry Point]
     │
     ├─ ESP32-CAM (face recognition)
     └─ Separate ESP32 with RFID/PIR
```
Cost: Rs. 500 + Rs. 350 = Rs. 850 per entrance

### Strategy 2: Dual-Purpose (PIR + Camera)
```
[Entry Point]
     │
     └─ ESP32-CAM with PIR
        (No RFID due to pin limitations)
```
Cost: Rs. 600 per entrance
Use case: Universities with student photos in database

### Strategy 3: Hybrid Verification
```
[Entry Point]
     │
     ├─ ESP32 with RFID/PIR (primary)
     └─ ESP32-CAM (verification)
```
Highest accuracy, prevents proxy attendance

## Face Recognition Workflow

```
1. PIR detects motion
2. Camera captures image
3. Detect face in image
4. Compare with database
5. If match: Publish to MQTT with student_id
6. Backend logs attendance
```

## Database Schema Addition

```sql
CREATE TABLE face_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(20),
    face_encoding BLOB,  -- 128-dimensional face embedding
    photo_url VARCHAR(255),
    trained_at TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student(student_id)
);

CREATE TABLE camera_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(50),
    cluster_id INT,
    student_id VARCHAR(20),
    confidence FLOAT,
    image_path VARCHAR(255),
    timestamp TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);
```

## Detection Checklist

**Camera Detection Tests**:
```cpp
bool testCamera() {
    if (!hasCamera) return false;
    
    // Test 1: Capture frame
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
        Serial.println("Camera: Frame capture failed");
        return false;
    }
    
    // Test 2: Check resolution
    if (fb->width == 0 || fb->height == 0) {
        esp_camera_fb_return(fb);
        return false;
    }
    
    // Test 3: Check format
    if (fb->format != PIXFORMAT_JPEG) {
        Serial.println("Camera: Invalid format");
        esp_camera_fb_return(fb);
        return false;
    }
    
    esp_camera_fb_return(fb);
    Serial.println("Camera: All tests passed");
    return true;
}
```

## Power Considerations

**ESP32-CAM Power Draw**:
- Idle: ~80mA
- During capture: ~150-200mA
- With flash LED: ~300mA

**Solution**: Use 5V 2A power supply, not USB

## Advantages & Limitations

**Advantages**:
- No card needed
- Difficult to forge
- Works from distance (up to 2m)
- Captures attendance photo

**Limitations**:
- Requires good lighting
- Privacy concerns (requires consent)
- More expensive (Rs. 500 vs Rs. 200)
- Higher power consumption
- Slower than RFID scan

## Recommended Use Cases for Camera

**Good for**:
- Engineering colleges (tech-savvy)
- Exam halls (prevent impersonation)
- High-security areas
- Universities with photo databases

**Not recommended for**:
- Budget schools
- Privacy-sensitive environments
- Low-light areas
- Young students (face changes frequently)

## Complete Auto-Detection Summary

With camera support, the universal node detects:

1. **RFID** (SPI bus scan) - Primary
2. **PIR** (GPIO check) - Motion trigger
3. **BLE** (Config flag) - Smartphone support
4. **Camera** (Init test) - Face recognition

**Priority Order**:
1. RFID (most reliable, fastest)
2. Face (high accuracy, slower)
3. BLE (convenient, medium reliability)

**Best Configuration**:
- Schools: RFID + PIR
- Universities: RFID + PIR + Camera
- Tech institutions: All four methods

Cost: Rs. 200-1000 per node depending on modules
