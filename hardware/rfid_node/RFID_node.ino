#include <SPI.h>
#include <ESP8266HTTPClient.h>
#include <ESP8266WiFi.h>
#include <MFRC522.h>
#include "config.h"  // Configuration file with credentials

// Hardware pin definitions from config
#define rs_pin RFID_RST_PIN
#define ss_pin RFID_SS_PIN
#define m_sensor PIR_SENSOR_PIN

// Initialize RFID reader
MFRC522 reader(ss_pin, rs_pin);

// State variables
int PIR_val = 0;
int flag = 0;
int sensor_state;
unsigned long lastMotionTime = 0;

void setup() {
  Serial.begin(115200);
  delay(500);
  
  // Initialize SPI and RFID
  SPI.begin();
  reader.PCD_Init();
  
  // WiFi setup with timeout
  connectWiFi();
  
  // Pin configuration
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(m_sensor, INPUT);
  
  digitalWrite(LED_BUILTIN, HIGH);  // LED off initially
  
  Serial.println("RFID Node initialized successfully");
  Serial.print("Device: ");
  Serial.println(DEVICE_NAME);
}

/**
 * Connect to WiFi with timeout
 */
void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  Serial.print("Connecting to WiFi");
  unsigned long startTime = millis();
  
  while (WiFi.status() != WL_CONNECTED) {
    if (millis() - startTime > WIFI_CONNECT_TIMEOUT) {
      Serial.println("\nWiFi connection timeout! Restarting...");
      ESP.restart();
    }
    delay(500);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.print("Connected to: ");
  Serial.println(WIFI_SSID);
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

/**
 * Post data to server with error handling
 */
bool post_data(String data) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected! Reconnecting...");
    connectWiFi();
    return false;
  }
  
  HTTPClient http;
  WiFiClient client;
  
  String url = "http://" + String(SERVER_IP) + String(API_ENDPOINT);
  
  http.begin(client, url);
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");
  http.setTimeout(5000);  // 5 second timeout
  
  int httpCode = http.POST(data);
  
  if (httpCode > 0) {
    String payload = http.getString();
    Serial.print("HTTP Response: ");
    Serial.print(httpCode);
    Serial.print(" - ");
    Serial.println(payload);
    http.end();
    return true;
  } else {
    Serial.print("HTTP POST failed, error: ");
    Serial.println(http.errorToString(httpCode));
    http.end();
    return false;
  }
}

/**
 * Read RFID card UID
 */
String readRFID() {
  if (!reader.PICC_IsNewCardPresent()) {
    return "";
  }
  
  if (!reader.PICC_ReadCardSerial()) {
    Serial.println("Failed to read card serial");
    return "";
  }
  
  String content = "";
  for (byte i = 0; i < reader.uid.size; i++) {
    content.concat(String(reader.uid.uidByte[i] < 0x10 ? " 0" : " "));
    content.concat(String(reader.uid.uidByte[i], HEX));
  }
  
  content.toUpperCase();
  return content.substring(1);  // Remove leading space
}

void loop() {
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected! Reconnecting...");
    connectWiFi();
  }
  
  sensor_state = digitalRead(m_sensor);
  
  if (sensor_state == HIGH) {
    unsigned long currentTime = millis();
    
    // Debounce check
    if (currentTime - lastMotionTime < DEBOUNCE_DELAY) {
      return;
    }
    
    delay(1000);  // Wait for person to present card
    
    String rfid_uid = readRFID();
    
    if (rfid_uid.length() > 0) {
      Serial.print("RFID detected: ");
      Serial.println(rfid_uid);
      
      if (flag == 0) {
        // Build data payload
        String data = "user_name=" + String(DEVICE_NAME) +
                      "&cluster_id=" + String(CLUSTER_ID) +
                      "&device_DATA=activated" +
                      "&sensor=true" +
                      "&id=" + rfid_uid;
        
        Serial.println("Sending data...");
        
        if (post_data(data)) {
          digitalWrite(LED_BUILTIN, LOW);  // LED on = success
          Serial.println("Data sent successfully");
          flag++;
          lastMotionTime = currentTime;
        } else {
          Serial.println("Failed to send data");
        }
      }
    }
    
    delay(DEBOUNCE_DELAY);
    flag = 0;
    digitalWrite(LED_BUILTIN, HIGH);  // LED off
  }
  
  delay(100);  // Small delay to prevent excessive loop speed
}
