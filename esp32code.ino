#include <WiFi.h>
#include <HTTPClient.h>
#include <Arduino_JSON.h>

const char* ssid = "SSID";
const char* password = "PWD";
const char* serverURL = "IP";  // Replace with your server's IP and port

const int numSamples = 256;  // Number of samples to collect
float voltageData[numSamples];
float currentData[numSamples];

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  // Connect to WiFi
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("Connected to WiFi");
  Serial.println(WiFi.localIP());
}

void loop() {
  // Collect voltage and current samples
  for (int i = 0; i < numSamples; i++) {
    voltageData[i] = analogRead(34);  // Example ADC pin for voltage
    currentData[i] = analogRead(35);  // Example ADC pin for current
    delay(10);  // Adjust sampling rate as needed
  }

  // Send the data to the server
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");

    // Create JSON data using Arduino_JSON.h
    JSONVar jsonData;
    JSONVar voltageArray;
    JSONVar currentArray;

    // Populate voltage and current arrays
    for (int i = 0; i < numSamples; i++) {
      voltageArray[i] = voltageData[i];
      currentArray[i] = currentData[i];
    }

    jsonData["voltage"] = voltageArray;
    jsonData["current"] = currentArray;

    // Convert JSON object to string
    String jsonString = JSON.stringify(jsonData);

    // Send the POST request with JSON payload
    int httpResponseCode = http.POST(jsonString);

    // Check response from the server
    if (httpResponseCode > 0) {
      Serial.printf("Data sent successfully: %d\n", httpResponseCode);
    } else {
      Serial.printf("Failed to send data: %d\n", httpResponseCode);
    }

    http.end();
  } else {
    Serial.println("WiFi not connected");
  }

  delay(5000);  // Wait before sending the next batch of data
}
