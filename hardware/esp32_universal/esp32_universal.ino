/*
 * ZIAS - ESP32 Universal Node with Hardware Auto-Detection
 * Supports: RFID (MFRC522), PIR Sensor, BLE Beacon
 * 
 * Hardware auto-detection:
 * - Checks I2C/SPI bus for RFID reader
 * - Checks GPIO for PIR sensor
 * - Enables BLE if configured
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
#include "config.h"

// Hardware detection flags
bool hasRFID = false;
bool hasPIR = false;
bool hasBLE = false;

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
 */
void detectHardware() {
  Serial.println("\n--- Hardware Detection ---");
  
  // Try to detect RFID reader on SPI bus
  SPI.begin();
  MFRC522 testRFID(RFID_SS_PIN, RFID_RST_PIN);
  testRFID.PCD_Init();
  delay(100);
  
  byte version = testRFID.PCD_ReadRegister(MFRC522::VersionReg);
  if (version == 0x91 || version == 0x92) {
    hasRFID = true;
    Serial.println("[✓] RFID Reader detected (MFRC522)");
  } else {
    Serial.println("[✗] RFID Reader not found");
  }
  
  // Detect PIR sensor (check if pin is configured)
  pinMode(PIR_SENSOR_PIN, INPUT);
  delay(100);
  int pirState = digitalRead(PIR_SENSOR_PIN);
  // Assume PIR is present if configured (can't reliably auto-detect)
  hasPIR = true;  // Always enable if pin is defined
  Serial.println("[✓] PIR Sensor enabled");
  
  // BLE is optional - enable only if configured in config.h
  #ifdef ENABLE_BLE
    hasBLE = true;
    Serial.println("[✓] BLE Beacon enabled (configured)");
  #else
    Serial.println("[✗] BLE Beacon disabled in config");
  #endif
  
  Serial.println("--------------------------\n");
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
 * Publish device status
 */
void publishDeviceStatus(String status) {
  StaticJsonDocument<256> doc;
  doc["device_id"] = DEVICE_NAME;
  doc["status"] = status;
  doc["has_rfid"] = hasRFID;
  doc["has_pir"] = hasPIR;
  doc["has_ble"] = hasBLE;
  doc["ip"] = WiFi.localIP().toString();
  doc["rssi"] = WiFi.RSSI();
  
  String payload;
  serializeJson(doc, payload);
  
  String topic = String(MQTT_TOPIC_PREFIX) + "/devices/" + String(DEVICE_NAME) + "/status";
  mqttClient.publish(topic.c_str(), payload.c_str());
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
