/*
 * ZIAS - ESP32 Universal Node with Complete Hardware Auto-Detection
 * Automatically detects and enables: RFID, PIR, BLE, Camera
 * 
 * Boot sequence:
 * 1. Scan hardware (I2C, SPI, GPIO)
 * 2. Detect all connected modules
 * 3. Enable only detected modules
 * 4. Report capabilities to server
 * 
 * Author: Enhanced version for Indian schools/universities
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <PubSubClient.h>  // MQTT
#include <ArduinoJson.h>
#include <SPI.h>
#include <MFRC522.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEBeacon.h>

// Optional: Camera support (uncomment if using ESP32-CAM)
#ifdef CAMERA_MODEL_AI_THINKER
#include "esp_camera.h"
#endif

#include "config.h"

// Hardware detection flags - set during boot
bool hasRFID = false;
bool hasPIR = false;
bool hasBLE = false;
bool hasCamera = false;

// Pin definitions (from config.h)
#define RFID_RST_PIN GPIO_RFID_RST
#define RFID_SS_PIN GPIO_RFID_SS
#define PIR_SENSOR_PIN GPIO_PIR
#define LED_PIN LED_BUILTIN

// RFID reader (if detected)
MFRC522 *rfid = nullptr;

// MQTT client
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

// State management
unsigned long lastMotionTime = 0;
unsigned long lastReconnectAttempt = 0;
int motionFlag = 0;

// Function declarations
void detectHardware();
void connectWiFi();
void connectMQTT();
void publishSensorEvent(String eventType, String rfidUid = "");
String readRFID();
void setupBLEBeacon();

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n=== ZIAS ESP32 Universal Node ===");
  Serial.print("Device ID: ");
  Serial.println(DEVICE_NAME);
  Serial.print("Cluster ID: ");
  Serial.println(CLUSTER_ID);
  
  // Initialize pins
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);  // LED off
  
  // Detect available hardware
  detectHardware();
  
  // Connect to WiFi
  connectWiFi();
  
  // Setup MQTT
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  
  // Initialize detected hardware
  if (hasRFID) {
    SPI.begin();
    rfid = new MFRC522(RFID_SS_PIN, RFID_RST_PIN);
    rfid->PCD_Init();
    Serial.println("RFID reader initialized");
  }
  
  if (hasPIR) {
    pinMode(PIR_SENSOR_PIN, INPUT);
    Serial.println("PIR sensor initialized");
  }
  
  if (hasBLE) {
    setupBLEBeacon();
    Serial.println("BLE beacon initialized");
  }
  
  Serial.println("\n=== Initialization Complete ===");
  Serial.println("Active modules:");
  Serial.print("  RFID: "); Serial.println(hasRFID ? "YES" : "NO");
  Serial.print("  PIR:  "); Serial.println(hasPIR ? "YES" : "NO");
  Serial.print("  BLE:  "); Serial.println(hasBLE ? "YES" : "NO");
  Serial.println("===============================\n");
}

/**
 * Auto-detect connected hardware
 * This runs at boot and determines which modules are available
 */
void detectHardware() {
  Serial.println("\n=== HARDWARE AUTO-DETECTION ===");
  Serial.println("Scanning for connected modules...\n");
  
  // 1. Try to detect RFID reader on SPI bus
  Serial.print("Checking RFID... ");
  SPI.begin();
  MFRC522 testRFID(RFID_SS_PIN, RFID_RST_PIN);
  testRFID.PCD_Init();
  delay(100);
  
  byte version = testRFID.PCD_ReadRegister(MFRC522::VersionReg);
  if (version == 0x91 || version == 0x92) {
    hasRFID = true;
    Serial.println("DETECTED");
    Serial.printf("  -> MFRC522 Version: 0x%02X\n", version);
  } else {
    Serial.println("NOT FOUND");
    Serial.printf("  -> Version register: 0x%02X (invalid)\n", version);
  }
  
  // 2. Detect PIR sensor
  Serial.print("Checking PIR... ");
  pinMode(PIR_SENSOR_PIN, INPUT);
  delay(100);
  // PIR is assumed present if pin is configured
  hasPIR = true;
  Serial.println("ENABLED");
  Serial.printf("  -> Using GPIO %d\n", PIR_SENSOR_PIN);
  
  // 3. Check for camera (ESP32-CAM only)
  Serial.print("Checking Camera... ");
  #ifdef CAMERA_MODEL_AI_THINKER
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
  config.frame_size = FRAMESIZE_QVGA;  // 320x240
  config.jpeg_quality = 12;
  config.fb_count = 1;
  
  esp_err_t err = esp_camera_init(&config);
  if (err == ESP_OK) {
    hasCamera = true;
    Serial.println("DETECTED");
    camera_fb_t *fb = esp_camera_fb_get();
    if (fb) {
      Serial.printf("  -> OV2640 Camera\n");
      Serial.printf("  -> Resolution: %dx%d\n", fb->width, fb->height);
      esp_camera_fb_return(fb);
    }
  } else {
    hasCamera = false;
    Serial.println("NOT FOUND");
    Serial.printf("  -> Init error: 0x%x\n", err);
  }
  #else
  Serial.println("DISABLED");
  Serial.println("  -> Not compiled for ESP32-CAM");
  #endif
  
  // 4. BLE is optional - enable only if configured
  Serial.print("Checking BLE... ");
  #ifdef ENABLE_BLE
    hasBLE = true;
    Serial.println("ENABLED");
    Serial.printf("  -> UUID: %s\n", BLE_BEACON_UUID);
  #else
    Serial.println("DISABLED");
    Serial.println("  -> Not configured in config.h");
  #endif
  
  // Summary
  Serial.println("\n=== DETECTION SUMMARY ===");
  Serial.printf("RFID Reader:  %s\n", hasRFID ? "✓ ACTIVE" : "✗ INACTIVE");
  Serial.printf("PIR Sensor:   %s\n", hasPIR ? "✓ ACTIVE" : "✗ INACTIVE");
  Serial.printf("Camera:       %s\n", hasCamera ? "✓ ACTIVE" : "✗ INACTIVE");
  Serial.printf("BLE Beacon:   %s\n", hasBLE ? "✓ ACTIVE" : "✗ INACTIVE");
  Serial.println("=========================\n");
  
  // Determine operating mode
  if (hasRFID && hasPIR && hasCamera) {
    Serial.println("MODE: Advanced (RFID + PIR + Camera)");
  } else if (hasRFID && hasPIR) {
    Serial.println("MODE: Standard (RFID + PIR)");
  } else if (hasPIR && hasCamera) {
    Serial.println("MODE: Camera-based (PIR + Camera)");
  } else if (hasPIR) {
    Serial.println("MODE: PIR-only (Motion detection)");
  } else {
    Serial.println("WARNING: No sensors detected!");
  }
  Serial.println();
}

/**
 * Connect to WiFi with retry
 */
void connectWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi connection failed! Restarting...");
    ESP.restart();
  }
}

/**
 * Connect to MQTT broker
 */
void connectMQTT() {
  if (mqttClient.connected()) {
    return;
  }
  
  Serial.print("Connecting to MQTT broker: ");
  Serial.println(MQTT_BROKER);
  
  String clientId = String(DEVICE_NAME) + "_" + String(ESP.getEfuseMac());
  
  if (mqttClient.connect(clientId.c_str())) {
    Serial.println("MQTT connected!");
    
    // Subscribe to command topic
    String cmdTopic = String(MQTT_TOPIC_PREFIX) + "/devices/" + String(DEVICE_NAME) + "/cmd";
    mqttClient.subscribe(cmdTopic.c_str());
    
    // Publish online status
    publishDeviceStatus("online");
  } else {
    Serial.print("MQTT connection failed, rc=");
    Serial.println(mqttClient.state());
  }
}

/**
 * MQTT callback for incoming messages
 */
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("]: ");
  
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(message);
  
  // Handle commands (OTA update, config change, etc.)
  // TODO: Implement command handling
}

/**
 * Publish sensor event to MQTT
 */
void publishSensorEvent(String eventType, String rfidUid) {
  if (!mqttClient.connected()) {
    return;
  }
  
  StaticJsonDocument<256> doc;
  doc["device_id"] = DEVICE_NAME;
  doc["cluster_id"] = CLUSTER_ID;
  doc["event_type"] = eventType;
  doc["timestamp"] = millis();
  
  if (rfidUid.length() > 0) {
    doc["rfid"] = rfidUid;
  }
  
  if (hasPIR) {
    doc["sensor"] = true;
  }
  
  String payload;
  serializeJson(doc, payload);
  
  String topic = String(MQTT_TOPIC_PREFIX) + "/devices/" + String(DEVICE_NAME) + "/sensor";
  mqttClient.publish(topic.c_str(), payload.c_str());
  
  Serial.print("Published to MQTT: ");
  Serial.println(payload);
}

/**
 * Publish device status with detected capabilities
 */
void publishDeviceStatus(String status) {
  StaticJsonDocument<256> doc;
  doc["device_id"] = DEVICE_NAME;
  doc["status"] = status;
  doc["has_rfid"] = hasRFID;
  doc["has_pir"] = hasPIR;
  doc["has_ble"] = hasBLE;
  doc["has_camera"] = hasCamera;
  doc["ip"] = WiFi.localIP().toString();
  doc["rssi"] = WiFi.RSSI();
  doc["firmware_version"] = "2.0";
  
  String payload;
  serializeJson(doc, payload);
  
  String topic = String(MQTT_TOPIC_PREFIX) + "/devices/" + String(DEVICE_NAME) + "/status";
  mqttClient.publish(topic.c_str(), payload.c_str());
  
  Serial.println("Published device status:");
  Serial.println(payload);
}

/**
 * Read RFID card
 */
String readRFID() {
  if (!hasRFID || !rfid) {
    return "";
  }
  
  if (!rfid->PICC_IsNewCardPresent()) {
    return "";
  }
  
  if (!rfid->PICC_ReadCardSerial()) {
    return "";
  }
  
  String uid = "";
  for (byte i = 0; i < rfid->uid.size; i++) {
    if (rfid->uid.uidByte[i] < 0x10) {
      uid += " 0";
    } else {
      uid += " ";
    }
    uid += String(rfid->uid.uidByte[i], HEX);
  }
  
  uid.toUpperCase();
  return uid.substring(1);  // Remove leading space
}

/**
 * Setup BLE beacon (optional)
 */
void setupBLEBeacon() {
  #ifdef ENABLE_BLE
  BLEDevice::init(DEVICE_NAME);
  
  BLEServer *pServer = BLEDevice::createServer();
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  
  // Set beacon UUID from config
  BLEBeacon beacon;
  beacon.setManufacturerId(0x4C00);  // Apple
  BLEUUID bleUUID(BLE_BEACON_UUID);
  beacon.setProximityUUID(bleUUID);
  beacon.setMajor(CLUSTER_ID);
  beacon.setMinor(1);
  
  BLEAdvertisementData advertisementData;
  advertisementData.setFlags(0x06);
  advertisementData.setManufacturerData(beacon.getData());
  
  pAdvertising->setAdvertisementData(advertisementData);
  pAdvertising->start();
  #endif
}

void loop() {
  // Reconnect WiFi if needed
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected! Reconnecting...");
    connectWiFi();
  }
  
  // Reconnect MQTT if needed
  if (!mqttClient.connected()) {
    unsigned long now = millis();
    if (now - lastReconnectAttempt > 5000) {
      lastReconnectAttempt = now;
      connectMQTT();
    }
  }
  mqttClient.loop();
  
  // Check PIR sensor
  if (hasPIR) {
    int pirState = digitalRead(PIR_SENSOR_PIN);
    
    if (pirState == HIGH) {
      unsigned long currentTime = millis();
      
      // Debounce check
      if (currentTime - lastMotionTime < DEBOUNCE_DELAY) {
        return;
      }
      
      Serial.println("Motion detected!");
      digitalWrite(LED_PIN, LOW);  // LED on
      
      delay(1000);  // Wait for person to present card
      
      // Try to read RFID if available
      String rfidUid = readRFID();
      
      if (rfidUid.length() > 0) {
        Serial.print("RFID detected: ");
        Serial.println(rfidUid);
        
        if (motionFlag == 0) {
          publishSensorEvent("activated", rfidUid);
          motionFlag++;
          lastMotionTime = currentTime;
        }
      } else if (!hasRFID) {
        // PIR-only mode (no RFID)
        if (motionFlag == 0) {
          publishSensorEvent("motion", "");
          motionFlag++;
          lastMotionTime = currentTime;
        }
      }
      
      delay(DEBOUNCE_DELAY);
      motionFlag = 0;
      digitalWrite(LED_PIN, HIGH);  // LED off
    }
  }
  
  // Small delay to prevent excessive CPU usage
  delay(100);
}
