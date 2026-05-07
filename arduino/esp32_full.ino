/*
  ╔══════════════════════════════════════════════════════╗
  ║  Havo Sifati Monitoringi — ESP32 To'liq Kodi v2.0  ║
  ║  Diplom ishi, 2025                                   ║
  ╠══════════════════════════════════════════════════════╣
  ║  Hozir ulangan:                                      ║
  ║    MQ-135 → GPIO 23 (DO, raqamli chiqish)           ║
  ║    MQ-2   → GPIO 22 (DO, raqamli chiqish)           ║
  ║                                                      ║
  ║  Kelajakda qo'shiladi:                               ║
  ║    MQ-7   → GPIO 21 (DO)                            ║
  ║    BME280 → I2C (SDA=21, SCL=22) — harorat/namlik  ║
  ║    SDS011 → UART — PM2.5, PM10                      ║
  ║    OLED   → I2C  — qurilmada ko'rsatish             ║
  ╠══════════════════════════════════════════════════════╣
  ║  Kerakli kutubxonalar (Arduino Library Manager):    ║
  ║    - ArduinoJson (Benoit Blanchon)                  ║
  ║  Kelajakda kerak bo'ladi:                           ║
  ║    - Adafruit BME280 Library                        ║
  ║    - Adafruit SSD1306                               ║
  ╚══════════════════════════════════════════════════════╝
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Kelajakdagi sensorlar uchun (hozir izoh):
// #include <Wire.h>
// #include <Adafruit_BME280.h>
// #include <Adafruit_SSD1306.h>
// #include <SoftwareSerial.h>   // SDS011 uchun

// ═══════════════════════════════════════════════════
// KONFIGURATSIYA — faqat shu bo'limni o'zgartiring!
// ═══════════════════════════════════════════════════

// Wi-Fi sozlamalari
const char* WIFI_SSID    = "SIZNING_WIFI_NOMI";       // <- o'zgartiring
const char* WIFI_PAROL   = "SIZNING_WIFI_PAROLI";     // <- o'zgartiring

// Server manzili (cmd > ipconfig > IPv4 Address ni ko'ring)
const char* SERVER_URL   = "http://192.168.1.100:8000/api/sensor";  // <- o'zgartiring

// Qurilma identifikatori (bir nechta qurilma bo'lsa farqlash uchun)
const char* QURILMA_ID   = "esp32_001";

// Ma'lumot yuborish oralig'i (millisekund)
const unsigned long YUBORISH_MS = 30000;  // 30 sekund

// ─── Sensorlarni yoqish/o'chirish ───
// Ulangan sensor = true, ulanmagan = false
const bool ENABLE_MQ135  = true;   // GPIO 23 — ULANGAN
const bool ENABLE_MQ2    = true;   // GPIO 22 — ULANGAN
const bool ENABLE_MQ7    = false;  // GPIO 21 — hali ulanmagan
const bool ENABLE_BME280 = false;  // I2C     — hali ulanmagan
const bool ENABLE_SDS011 = false;  // UART    — hali ulanmagan

// ═══════════════════════════════════════════════════
// GPIO PINLARI
// ═══════════════════════════════════════════════════
const int MQ135_PIN = 23;
const int MQ2_PIN   = 22;
const int MQ7_PIN   = 21;

// ═══════════════════════════════════════════════════
// GLOBAL O'ZGARUVCHILAR
// ═══════════════════════════════════════════════════
unsigned long oxirgi_yuborish = 0;
int yuborish_soni  = 0;
int xato_soni      = 0;

// ─── Sensor ma'lumotlari strukturasi ───
struct SensorData {
  int   mq135   = -1;      // -1 = o'chirilgan (null)
  int   mq2     = -1;
  int   mq7     = -1;
  float harorat = NAN;     // NAN = o'chirilgan (null)
  float namlik  = NAN;
  float bosim   = NAN;
  float pm25    = NAN;
  float pm10    = NAN;
};

// ═══════════════════════════════════════════════════
// WI-FI GA ULANISH
// ═══════════════════════════════════════════════════
void wifi_ga_ulan() {
  Serial.print("📡 Wi-Fi ga ulanilmoqda: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PAROL);

  int urinish = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    if (++urinish >= 40) {
      Serial.println("\n⚠️ Ulanib bo'lmadi! Qayta urinilmoqda...");
      WiFi.disconnect();
      delay(2000);
      WiFi.begin(WIFI_SSID, WIFI_PAROL);
      urinish = 0;
    }
  }

  Serial.println();
  Serial.println("✅ Wi-Fi ga ulandi!");
  Serial.print("   📍 IP manzili : "); Serial.println(WiFi.localIP());
  Serial.print("   📶 Signal     : "); Serial.print(WiFi.RSSI()); Serial.println(" dBm");
}

// ═══════════════════════════════════════════════════
// SENSORLARNI O'QISH
// ═══════════════════════════════════════════════════
SensorData sensorlar_oqi() {
  SensorData d;

  // ─ MQ-135 (CO₂, NH₃, Benzol) ─
  if (ENABLE_MQ135) {
    d.mq135 = digitalRead(MQ135_PIN);
    // DO: HIGH=1 (toza), LOW=0 (gaz aniqlandi)
  }

  // ─ MQ-2 (Metan, LPG, Tutun) ─
  if (ENABLE_MQ2) {
    d.mq2 = digitalRead(MQ2_PIN);
  }

  // ─ MQ-7 (Uglerod oksidi CO) ─
  if (ENABLE_MQ7) {
    d.mq7 = digitalRead(MQ7_PIN);
  }

  // ─ BME280 (Harorat, Namlik, Bosim) — KELAJAKDA ─
  // if (ENABLE_BME280) {
  //   d.harorat = bme.readTemperature();
  //   d.namlik  = bme.readHumidity();
  //   d.bosim   = bme.readPressure() / 100.0F;
  // }

  // ─ SDS011 (PM2.5, PM10) — KELAJAKDA ─
  // if (ENABLE_SDS011) {
  //   sds.read(&d.pm25, &d.pm10);
  // }

  return d;
}

// ═══════════════════════════════════════════════════
// JSON YARATISH VA SERVERGA YUBORISH
// ═══════════════════════════════════════════════════
bool serverga_yubor(const SensorData& d) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ Wi-Fi yo'q — qayta ulanilmoqda...");
    wifi_ga_ulan();
    return false;
  }

  // JSON hujjati (256 bayt yetarli)
  StaticJsonDocument<256> doc;
  doc["device_id"] = QURILMA_ID;

  // Sensor qiymatlari: -1 yoki NAN = null
  if (d.mq135 >= 0) doc["mq135"] = d.mq135; else doc["mq135"] = nullptr;
  if (d.mq2   >= 0) doc["mq2"]   = d.mq2;   else doc["mq2"]   = nullptr;
  if (d.mq7   >= 0) doc["mq7"]   = d.mq7;   else doc["mq7"]   = nullptr;

  if (!isnan(d.harorat)) doc["harorat"] = round(d.harorat * 10) / 10.0;
    else doc["harorat"] = nullptr;
  if (!isnan(d.namlik))  doc["namlik"]  = round(d.namlik * 10) / 10.0;
    else doc["namlik"]  = nullptr;
  if (!isnan(d.bosim))   doc["bosim"]   = round(d.bosim * 10) / 10.0;
    else doc["bosim"]   = nullptr;
  if (!isnan(d.pm25))    doc["pm25"]    = round(d.pm25 * 10) / 10.0;
    else doc["pm25"]    = nullptr;
  if (!isnan(d.pm10))    doc["pm10"]    = round(d.pm10 * 10) / 10.0;
    else doc["pm10"]    = nullptr;

  String json;
  serializeJson(doc, json);

  Serial.print("📤 Yuborilmoqda: ");
  Serial.println(json);

  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(10000);  // 10 sekund

  int kod = http.POST(json);

  if (kod == HTTP_CODE_OK || kod == HTTP_CODE_CREATED) {
    String javob = http.getString();
    Serial.print("✅ Server javobi (");
    Serial.print(kod);
    Serial.print("): ");
    Serial.println(javob);
    http.end();
    yuborish_soni++;
    xato_soni = 0;
    return true;
  } else if (kod > 0) {
    Serial.print("⚠️ HTTP xato kodi: ");
    Serial.println(kod);
  } else {
    Serial.print("❌ Ulanish xatosi: ");
    Serial.println(http.errorToString(kod));
  }

  http.end();
  xato_soni++;
  return false;
}

// ═══════════════════════════════════════════════════
// SENSOR HOLATINI SERIAL MONITOR GA CHIQARISH
// ═══════════════════════════════════════════════════
void holat_chiqar(const SensorData& d) {
  Serial.println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");

  if (d.mq135 >= 0) {
    Serial.print("🏭 MQ-135 (CO₂/NH₃/Benzol): ");
    Serial.println(d.mq135 == 1 ? "✅ TOZA" : "🚨 GAZ ANIQLANDI!");
  }
  if (d.mq2 >= 0) {
    Serial.print("🔥 MQ-2   (Metan/LPG)     : ");
    Serial.println(d.mq2 == 1 ? "✅ TOZA" : "🚨 GAZ ANIQLANDI!");
  }
  if (d.mq7 >= 0) {
    Serial.print("💨 MQ-7   (CO)            : ");
    Serial.println(d.mq7 == 1 ? "✅ TOZA" : "🚨 CO ANIQLANDI!");
  }
  if (!isnan(d.harorat)) {
    Serial.print("🌡️  Harorat               : ");
    Serial.print(d.harorat, 1); Serial.println(" °C");
  }
  if (!isnan(d.namlik)) {
    Serial.print("💧 Namlik                : ");
    Serial.print(d.namlik, 1); Serial.println(" %");
  }
  if (!isnan(d.pm25)) {
    Serial.print("🔴 PM2.5                 : ");
    Serial.print(d.pm25, 1); Serial.println(" μg/m³");
  }

  Serial.print("📊 Jami yuborildi: "); Serial.print(yuborish_soni);
  Serial.print(" | Xato: "); Serial.println(xato_soni);
  Serial.println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
}

// ═══════════════════════════════════════════════════
// SETUP — bir marta ishga tushadi
// ═══════════════════════════════════════════════════
void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("\n╔══════════════════════════════════════════╗");
  Serial.println("║   Havo Sifati Monitoringi — ESP32 v2    ║");
  Serial.println("║   Diplom loyihasi, 2025                 ║");
  Serial.println("╚══════════════════════════════════════════╝\n");

  // ─ GPIO pinlarini sozlash ─
  if (ENABLE_MQ135) { pinMode(MQ135_PIN, INPUT); Serial.println("✅ MQ-135 sozlandi (GPIO 23)"); }
  if (ENABLE_MQ2)   { pinMode(MQ2_PIN,   INPUT); Serial.println("✅ MQ-2   sozlandi (GPIO 22)"); }
  if (ENABLE_MQ7)   { pinMode(MQ7_PIN,   INPUT); Serial.println("✅ MQ-7   sozlandi (GPIO 21)"); }

  // ─ Wi-Fi ─
  wifi_ga_ulan();

  Serial.print("\n⏱️  Yuborish oralig'i : ");
  Serial.print(YUBORISH_MS / 1000);
  Serial.println(" sekund");
  Serial.print("🖥️  Server manzili   : ");
  Serial.println(SERVER_URL);
  Serial.println("✨ Qurilma tayyor!\n");

  // Birinchi o'lchovni darhol yuborish
  oxirgi_yuborish = millis() - YUBORISH_MS;
}

// ═══════════════════════════════════════════════════
// LOOP — doimo takrorlanadi
// ═══════════════════════════════════════════════════
void loop() {
  unsigned long hozir = millis();

  if (hozir - oxirgi_yuborish >= YUBORISH_MS) {
    oxirgi_yuborish = hozir;

    // Sensorlarni o'qib, serial ga chiqarib, serverga yuborish
    SensorData d = sensorlar_oqi();
    holat_chiqar(d);

    if (!serverga_yubor(d)) {
      Serial.println("⚠️ Keyingi urinishda qayta yuboriladi.\n");
    } else {
      Serial.print("⏳ Keyingi o'lchov ");
      Serial.print(YUBORISH_MS / 1000);
      Serial.println(" sekunddan so'ng.\n");
    }
  }

  // Wi-Fi uzilishini kuzatish
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ Wi-Fi uzildi! Qayta ulanilmoqda...");
    wifi_ga_ulan();
  }

  delay(100);  // protsessor yukini kamaytirish
}
