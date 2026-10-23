#include <WiFi.h>

const unsigned long SCAN_INTERVAL_MS = 8000;
unsigned long lastScan = 0;
unsigned long sampleId = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(200);
  Serial.println("{\"status\":\"ESP32 monitor started\"}");
}

void loop() {
  if (millis() - lastScan < SCAN_INTERVAL_MS) {
    delay(50);
    return;
  }
  lastScan = millis();

  int n = WiFi.scanNetworks(false, true);
  int strongest = -100;
  int totalRSSI = 0;
  int channelMask = 0;
  int valid = 0;

  if (n >= 0) {
    for (int i = 0; i < n; i++) {
      int rssi = WiFi.RSSI(i);
      int channel = WiFi.channel(i);
      if (rssi > strongest) strongest = rssi;
      totalRSSI += rssi;
      valid++;
      if (channel >= 1 && channel <= 14) {
        channelMask |= (1 << (channel - 1));
      }
    }
  }

  int avgRSSI = valid > 0 ? totalRSSI / valid : 0;
  int channels = 0;
  for (int i = 0; i < 14; i++) {
    if (channelMask & (1 << i)) channels++;
  }

  Serial.printf(
    "{\"sample\":%lu,\"uptime_ms\":%lu,\"networks\":%d,\"strongest_rssi\":%d,\"avg_rssi\":%d,\"channels\":%d}\n",
    ++sampleId, millis(), valid, valid > 0 ? strongest : 0, avgRSSI, channels
  );
  WiFi.scanDelete();
}
