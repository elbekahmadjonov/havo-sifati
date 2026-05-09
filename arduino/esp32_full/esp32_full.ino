/*
  ╔══════════════════════════════════════════════════════════════╗
  ║   HAVO SIFATI MONITORINGI — ESP32 To'liq Versiya v3.0      ║
  ║   Diplom ishi, 2025-2026                                    ║
  ╠══════════════════════════════════════════════════════════════╣
  ║   Ulangan sensorlar:                                        ║
  ║     MQ-135 → GPIO 23  (DO, raqamli) — CO₂/NH₃/Benzol      ║
  ║     MQ-2   → GPIO 5   (DO, raqamli) — Metan/LPG/Tutun      ║
  ║     MQ-7   → GPIO 19  (DO, raqamli) — Uglerod oksidi (CO)  ║
  ║     DHT22  → GPIO 4   (data)        — Harorat va namlik     ║
  ║     OLED   → SDA=21, SCL=22 (I2C, 0x3C)                   ║
  ╠══════════════════════════════════════════════════════════════╣
  ║   Kerakli kutubxonalar (Arduino Library Manager):           ║
  ║     - ArduinoJson (Benoit Blanchon) v6+                     ║
  ║     - DHT sensor library (Adafruit)                         ║
  ║     - Adafruit SSD1306                                      ║
  ║     - Adafruit GFX Library                                  ║
  ╠══════════════════════════════════════════════════════════════╣
  ║   Kelajakda qo'shilishi mumkin (hozir izohlangan):          ║
  ║     - BMP280  → I2C (0x76/0x77) — harorat, namlik, bosim   ║
  ║     - SDS011  → UART (RX=16, TX=17) — PM2.5, PM10          ║
  ╚══════════════════════════════════════════════════════════════╝
*/

// ═══════════════════════════════════════════════════════════════
// KUTUBXONALAR
// ═══════════════════════════════════════════════════════════════
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// Kelajakdagi sensorlar uchun (hozir izoh, kerak bo'lganda oching):
// #include <Adafruit_BMP280.h>      // BMP280 — harorat, bosim
// #include <SoftwareSerial.h>       // SDS011 uchun UART

// ═══════════════════════════════════════════════════════════════
// KONFIGURATSIYA — FAQAT SHU BO'LIMNI O'ZGARTIRING!
// ═══════════════════════════════════════════════════════════════

// Wi-Fi sozlamalari
const char* WIFI_SSID     = "esp32";       // <- o'zgartiring
const char* WIFI_PASSWORD = "12123434";     // <- o'zgartiring

// Server manzili (cmd → ipconfig → IPv4 Address ni ko'ring)
const char* SERVER_URL    = "http://192.168.62.245:8000/api/sensor";

// Qurilma identifikatori (bir nechta ESP32 bo'lsa farqlash uchun)
const char* DEVICE_ID     = "esp32_001";

// Ma'lumot yuborish oralig'i (millisekund)
const unsigned long YUBORISH_INTERVALI = 30000;   // 30 sekund

// OLED sahifa almashish vaqti (millisekund)
const unsigned long SAHIFA_INTERVAL    = 5000;    // 5 sekund

// Wi-Fi qayta ulanish oralig'i (oflayn rejimda)
const unsigned long QAYTA_ULANISH_MS   = 30000;   // 30 sekund

// ─── Sensorlarni yoqish / o'chirish ──────────────────────────
// Ulangan sensor = true  |  Ulanmagan sensor = false
const bool ENABLE_MQ135  = true;    // GPIO 23 — ULANGAN
const bool ENABLE_MQ2    = true;    // GPIO 5  — ULANGAN
const bool ENABLE_MQ7    = true;    // GPIO 19 — ULANGAN
const bool ENABLE_DHT22  = true;    // GPIO 4  — ULANGAN
const bool ENABLE_OLED   = true;    // I2C (21/22) — ULANGAN

// Kelajakdagi sensorlar (false qoldirilgan, hozir ulanmagan):
// const bool ENABLE_BMP280 = false;   // I2C (0x76) — BMP280
// const bool ENABLE_SDS011 = false;   // UART (16/17) — SDS011

// ═══════════════════════════════════════════════════════════════
// GPIO PINLARI
// ═══════════════════════════════════════════════════════════════
const int MQ135_PIN = 23;    // MQ-135 raqamli chiqishi (DO)
const int MQ2_PIN   = 5;     // MQ-2   raqamli chiqishi (DO)
const int MQ7_PIN   = 19;    // MQ-7   raqamli chiqishi (DO)
const int DHT22_PIN = 4;     // DHT22  data pini
#define   DHT_TYPE  DHT22    // DHT sensor turi

// OLED ekran sozlamalari
#define OLED_WIDTH   128     // Piksel eni
#define OLED_HEIGHT  64      // Piksel balandligi
#define OLED_ADDRESS 0x3C    // I2C manzil (alternativ: 0x3D)
#define OLED_RESET   -1      // Reset pini (-1 = ESP32 ichki reset)

// Kelajakdagi qurilmalar uchun joy (hozir izoh):
// #define BMP280_ADDRESS 0x76   // BMP280 I2C manzili
// #define SDS011_RX_PIN  16     // SDS011 RX pini
// #define SDS011_TX_PIN  17     // SDS011 TX pini

// ═══════════════════════════════════════════════════════════════
// OBYEKTLAR
// ═══════════════════════════════════════════════════════════════
DHT           dht(DHT22_PIN, DHT_TYPE);
Adafruit_SSD1306 oled(OLED_WIDTH, OLED_HEIGHT, &Wire, OLED_RESET);

// Kelajakdagi obyektlar (hozir izoh):
// Adafruit_BMP280 bmp;
// SoftwareSerial  sdsSerial(SDS011_RX_PIN, SDS011_TX_PIN);

// ═══════════════════════════════════════════════════════════════
// GLOBAL O'ZGARUVCHILAR
// ═══════════════════════════════════════════════════════════════
unsigned long oxirgi_yuborish    = 0;       // Oxirgi yuborish vaqti (ms)
unsigned long oxirgi_sahifa_alm  = 0;       // OLED sahifa almashish vaqti
unsigned long oxirgi_oled_draw   = 0;       // OLED oxirgi chizilgan vaqt
unsigned long oxirgi_qayta_ulan  = 0;       // Wi-Fi qayta ulanish vaqti

int  joriy_sahifa    = 0;       // Hozirgi OLED sahifasi: 0, 1, 2
int  yuborish_soni   = 0;       // Muvaffaqiyatli yuborishlar soni
int  xato_soni       = 0;       // Ketma-ket xatolar soni
bool server_ulangan  = false;   // Oxirgi yuborish holati
bool wifi_ulangan    = false;   // Joriy Wi-Fi holati
char oxirgi_vaqt[9]  = "--:--"; // Oxirgi yuborish vaqti (MM:SS from start)

// ─── Sensor ma'lumotlari strukturasi ─────────────────────────
struct SensorData {
  int   mq135   = -1;       // -1 = o'chirilgan yoki xato (null yuboriladi)
  int   mq2     = -1;
  int   mq7     = -1;
  float harorat = NAN;      // NAN = o'chirilgan yoki xato (null yuboriladi)
  float namlik  = NAN;
  float bosim   = NAN;      // BMP280 uchun (kelajak)
  float pm25    = NAN;      // SDS011 uchun (kelajak)
  float pm10    = NAN;      // SDS011 uchun (kelajak)
};

SensorData joriy_data;      // Oxirgi o'lchov natijasi (OLED uchun global)

// ═══════════════════════════════════════════════════════════════
// YORDAMCHI: VAQTNI FORMATLASH (millis() dan MM:SS)
// ═══════════════════════════════════════════════════════════════
void vaqt_yangilash() {
  unsigned long jami_sekund = millis() / 1000;
  int minut  = (jami_sekund / 60) % 60;
  int sekund = jami_sekund % 60;
  snprintf(oxirgi_vaqt, sizeof(oxirgi_vaqt), "%02d:%02d", minut, sekund);
}

// ═══════════════════════════════════════════════════════════════
// UMUMIY HAVO SIFATI HOLATI
// ═══════════════════════════════════════════════════════════════
const char* holat_aniqlash(const SensorData& d) {
  if ((ENABLE_MQ135 && d.mq135 == 0) ||
      (ENABLE_MQ2   && d.mq2   == 0) ||
      (ENABLE_MQ7   && d.mq7   == 0)) {
    return "XAVFLI";
  }
  return "YAXSHI";
}

// ═══════════════════════════════════════════════════════════════
// WI-FI ULANISH — setup() da bloklovchi ulanish
// ═══════════════════════════════════════════════════════════════
void wifi_ga_ulan() {
  Serial.print("\n📡 Wi-Fi ga ulanilmoqda: ");
  Serial.println(WIFI_SSID);

  if (ENABLE_OLED) {
    oled.clearDisplay();
    oled.setTextSize(1);
    oled.setTextColor(SSD1306_WHITE);
    oled.setCursor(0, 0);
    oled.println("WiFi ulanilmoqda...");
    oled.println(WIFI_SSID);
    oled.display();
  }

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int  urinish = 0;
  int  nuqta   = 0;

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    nuqta++;

    // Har 2 sekundda OLED yangilash
    if (ENABLE_OLED && nuqta % 4 == 0) {
      oled.clearDisplay();
      oled.setCursor(0, 0);
      oled.println("WiFi ulanilmoqda...");
      oled.print(WIFI_SSID);
      oled.setCursor(0, 20);
      oled.print("Urinish: ");
      oled.println(urinish + 1);
      oled.setCursor(0, 30);
      for (int i = 0; i < (nuqta / 4) % 6; i++) oled.print(".");
      oled.display();
    }

    if (++urinish >= 40) {   // 20 sekund: qayta urinish
      Serial.println("\n⚠️  20s kutildi, qayta urinilmoqda...");
      WiFi.disconnect();
      delay(2000);
      WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
      urinish = 0;
    }
  }

  wifi_ulangan = true;
  Serial.println();
  Serial.println("✅ Wi-Fi ga ulandi!");
  Serial.print("   📍 IP manzili  : "); Serial.println(WiFi.localIP());
  Serial.print("   📶 Signal kuchi : "); Serial.print(WiFi.RSSI()); Serial.println(" dBm");
  Serial.print("   🌐 Gateway      : "); Serial.println(WiFi.gatewayIP());

  if (ENABLE_OLED) {
    oled.clearDisplay();
    oled.setCursor(0, 0);
    oled.println("WiFi ulandi! ✓");
    oled.print("IP: "); oled.println(WiFi.localIP());
    oled.print("Signal: "); oled.print(WiFi.RSSI()); oled.println(" dBm");
    oled.display();
    delay(2000);
  }
}

// ═══════════════════════════════════════════════════════════════
// WI-FI URINISH — bloklanmaydigan (15s kutadi, bo'lmasa oflayn)
// ═══════════════════════════════════════════════════════════════
bool wifi_urinib_kor() {
  Serial.print("\n📡 Wi-Fi ga ulanilmoqda: ");
  Serial.println(WIFI_SSID);

  if (ENABLE_OLED) {
    oled.clearDisplay();
    oled.setCursor(0, 0);
    oled.println("WiFi ulanilmoqda...");
    oled.println(WIFI_SSID);
    oled.display();
  }

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  // 15 sekund kutatamiz (30 × 500ms)
  for (int i = 0; i < 30; i++) {
    delay(500);
    Serial.print(".");
    if (WiFi.status() == WL_CONNECTED) {
      wifi_ulangan = true;
      Serial.println();
      Serial.println("✅ Wi-Fi ga ulandi!");
      Serial.print("   📍 IP: "); Serial.println(WiFi.localIP());

      if (ENABLE_OLED) {
        oled.clearDisplay();
        oled.setCursor(0, 0);
        oled.println("WiFi ulandi!");
        oled.print("IP: "); oled.println(WiFi.localIP());
        oled.display();
        delay(1500);
      }
      return true;
    }
  }

  // Ulanmadi — oflayn rejim
  wifi_ulangan = false;
  WiFi.disconnect();
  Serial.println();
  Serial.println("⚠️  WiFi yo'q — oflayn rejimda davom etiladi");
  Serial.println("   (Sensorlar o'qiladi, server ga yuborilmaydi)");

  if (ENABLE_OLED) {
    oled.clearDisplay();
    oled.setCursor(0, 0);
    oled.println("WiFi yo'q!");
    oled.println("Oflayn rejim");
    oled.println("");
    oled.println("Sensorlar ishlaydi.");
    oled.display();
    delay(2000);
  }
  return false;
}

// ═══════════════════════════════════════════════════════════════
// SENSORLARDAN O'QISH
// ═══════════════════════════════════════════════════════════════
SensorData sensorlar_oqi() {
  SensorData d;

  // ─── MQ-135 (CO₂, NH₃, Benzol) ────────────────────────────
  if (ENABLE_MQ135) {
    d.mq135 = digitalRead(MQ135_PIN);
    // DO: HIGH=1 → toza havo  |  LOW=0 → gaz aniqlandi
  }

  // ─── MQ-2 (Metan, LPG, Tutun, Vodorod) ────────────────────
  if (ENABLE_MQ2) {
    d.mq2 = digitalRead(MQ2_PIN);
  }

  // ─── MQ-7 (Uglerod oksidi — CO) ────────────────────────────
  if (ENABLE_MQ7) {
    d.mq7 = digitalRead(MQ7_PIN);
  }

  // ─── DHT22 (Harorat va Namlik) ──────────────────────────────
  if (ENABLE_DHT22) {
    float t = dht.readTemperature();
    float h = dht.readHumidity();

    if (!isnan(t)) {
      d.harorat = t;
    } else {
      Serial.println("⚠️  DHT22 harorat o'qilmadi — null yuboriladi");
    }
    if (!isnan(h)) {
      d.namlik = h;
    } else {
      Serial.println("⚠️  DHT22 namlik o'qilmadi — null yuboriladi");
    }
  }

  // ─── BMP280 (Harorat, Bosim) — KELAJAKDA ────────────────────
  // if (ENABLE_BMP280) {
  //   float t = bmp.readTemperature();
  //   float p = bmp.readPressure() / 100.0F;  // Pa → hPa
  //   if (!isnan(t) && t != 0) d.harorat = t;
  //   if (!isnan(p) && p  > 0) d.bosim   = p;
  // }

  // ─── SDS011 (PM2.5, PM10) — KELAJAKDA ──────────────────────
  // if (ENABLE_SDS011) {
  //   float pm25_val = 0, pm10_val = 0;
  //   // SDS011 kutubxona funksiyasiga qarab o'zgartiring:
  //   // if (sds.read(&pm25_val, &pm10_val) == 0) {
  //   //   d.pm25 = pm25_val;
  //   //   d.pm10 = pm10_val;
  //   // }
  // }

  return d;
}

// ═══════════════════════════════════════════════════════════════
// SERVERGA YUBORISH
// ═══════════════════════════════════════════════════════════════
bool serverga_yubor(const SensorData& d) {
  if (WiFi.status() != WL_CONNECTED) {
    wifi_ulangan = false;
    Serial.println("📵 Wi-Fi yo'q — yuborilmaydi, sensorlar o'qishda davom etadi");
    return false;
  }

  // JSON hujjat yaratish (384 bayt yetarli)
  StaticJsonDocument<384> doc;
  doc["device_id"] = DEVICE_ID;

  // Har bir sensor: -1 yoki NAN bo'lsa null yuboriladi
  if (ENABLE_MQ135 && d.mq135 >= 0) doc["mq135"] = d.mq135; else doc["mq135"] = nullptr;
  if (ENABLE_MQ2   && d.mq2   >= 0) doc["mq2"]   = d.mq2;   else doc["mq2"]   = nullptr;
  if (ENABLE_MQ7   && d.mq7   >= 0) doc["mq7"]   = d.mq7;   else doc["mq7"]   = nullptr;

  if (ENABLE_DHT22 && !isnan(d.harorat))
    doc["harorat"] = (float)round(d.harorat * 10) / 10.0f;
  else
    doc["harorat"] = nullptr;

  if (ENABLE_DHT22 && !isnan(d.namlik))
    doc["namlik"] = (float)round(d.namlik * 10) / 10.0f;
  else
    doc["namlik"] = nullptr;

  // Bosim (BMP280 ulanganda to'ldiriladi)
  if (!isnan(d.bosim))
    doc["bosim"] = (float)round(d.bosim * 10) / 10.0f;
  else
    doc["bosim"] = nullptr;

  // Zarrachalar (SDS011 ulanganda to'ldiriladi)
  if (!isnan(d.pm25)) doc["pm25"] = (float)round(d.pm25 * 10) / 10.0f; else doc["pm25"] = nullptr;
  if (!isnan(d.pm10)) doc["pm10"] = (float)round(d.pm10 * 10) / 10.0f; else doc["pm10"] = nullptr;

  String json;
  serializeJson(doc, json);

  Serial.print("📤 Yuborilmoqda → ");
  Serial.println(json);

  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(10000);  // 10 sekund kutish

  int kod = http.POST(json);

  if (kod == HTTP_CODE_OK || kod == HTTP_CODE_CREATED) {
    String javob = http.getString();
    Serial.print("✅ Server javobi (HTTP ");
    Serial.print(kod);
    Serial.print("): ");
    Serial.println(javob);
    http.end();

    yuborish_soni++;
    xato_soni     = 0;
    server_ulangan = true;
    wifi_ulangan   = true;
    vaqt_yangilash();
    return true;

  } else if (kod > 0) {
    Serial.print("⚠️  HTTP xato kodi: ");
    Serial.print(kod);
    Serial.print(" | Javob: ");
    Serial.println(http.getString());
  } else {
    Serial.print("❌ Ulanish xatosi: ");
    Serial.println(http.errorToString(kod));
  }

  http.end();
  xato_soni++;
  server_ulangan = false;
  return false;
}

// ═══════════════════════════════════════════════════════════════
// SERIAL MONITOR — BATAFSIL LOG
// ═══════════════════════════════════════════════════════════════
void serial_log(const SensorData& d) {
  Serial.println("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  Serial.print("📊 O'lchov #");
  Serial.print(yuborish_soni + 1);
  Serial.print("  |  Ishlash vaqti: ");
  Serial.print(millis() / 1000);
  Serial.println("s");
  Serial.println("──────────────────────────────────────────────");

  // Gaz sensorlari
  if (ENABLE_MQ135) {
    Serial.print("🏭 MQ-135 (CO₂/NH₃/Benzol)  : ");
    if (d.mq135 >= 0)
      Serial.println(d.mq135 == 1 ? "✅ TOZA  (gaz aniqlanmadi)" : "🚨 XAVF! GAZ ANIQLANDI!");
    else
      Serial.println("-- (o'qilmadi)");
  }
  if (ENABLE_MQ2) {
    Serial.print("🔥 MQ-2   (Metan/LPG/Tutun) : ");
    if (d.mq2 >= 0)
      Serial.println(d.mq2 == 1 ? "✅ TOZA  (gaz aniqlanmadi)" : "🚨 XAVF! GAZ ANIQLANDI!");
    else
      Serial.println("-- (o'qilmadi)");
  }
  if (ENABLE_MQ7) {
    Serial.print("💨 MQ-7   (Uglerod oksidi)  : ");
    if (d.mq7 >= 0)
      Serial.println(d.mq7 == 1 ? "✅ TOZA  (CO aniqlanmadi)" : "🚨 XAVF! CO ANIQLANDI!");
    else
      Serial.println("-- (o'qilmadi)");
  }

  Serial.println("──────────────────────────────────────────────");

  // Harorat va namlik
  if (ENABLE_DHT22) {
    Serial.print("🌡️  Harorat  : ");
    if (!isnan(d.harorat)) { Serial.print(d.harorat, 1); Serial.println(" °C"); }
    else                    Serial.println("❌ null (DHT22 xato)");

    Serial.print("💧 Namlik   : ");
    if (!isnan(d.namlik))  { Serial.print(d.namlik, 1); Serial.println(" %"); }
    else                    Serial.println("❌ null (DHT22 xato)");
  }

  // Bosim (BMP280 ulanganda chiqadi)
  if (!isnan(d.bosim)) {
    Serial.print("🌬️  Bosim    : "); Serial.print(d.bosim, 1); Serial.println(" hPa");
  }

  // Zarrachalar (SDS011 ulanganda chiqadi)
  if (!isnan(d.pm25)) {
    Serial.print("🔴 PM2.5    : "); Serial.print(d.pm25, 1); Serial.println(" μg/m³");
    Serial.print("🟠 PM10     : "); Serial.print(d.pm10, 1); Serial.println(" μg/m³");
  }

  Serial.println("──────────────────────────────────────────────");
  Serial.print("📶 Wi-Fi    : "); Serial.println(wifi_ulangan   ? "✅ Ulangan" : "❌ Uzilgan");
  Serial.print("🖥️  Server   : "); Serial.println(server_ulangan ? "✅ Javob berdi" : "❌ Ulangan emas");
  Serial.print("📈 Statistik: ");
  Serial.print(yuborish_soni); Serial.print(" muvaffaqiyat | ");
  Serial.print(xato_soni);     Serial.println(" ketma-ket xato");
  Serial.print("🏷️  Holat    : "); Serial.println(holat_aniqlash(d));
  Serial.println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
}

// ═══════════════════════════════════════════════════════════════
// OLED SAHIFA 1 — ASOSIY HOLAT
//
//  ┌──────────────┐
//  │ HAVO SIFATI  │
//  │──────────────│
//  │ T: 24.5°C    │
//  │ H: 45%       │
//  │ WiFi: Ulangan│
//  │──────────────│
//  │ Holat: YAXSHI│
//  └──────────────┘
// ═══════════════════════════════════════════════════════════════
void oled_sahifa1(const SensorData& d) {
  oled.clearDisplay();
  oled.setTextColor(SSD1306_WHITE);
  oled.setTextSize(1);

  // Sarlavha (markazda)
  oled.setCursor(16, 0);
  oled.println("HAVO SIFATI");
  oled.drawLine(0, 9, 127, 9, SSD1306_WHITE);

  // Harorat
  oled.setCursor(0, 13);
  oled.print("T: ");
  if (!isnan(d.harorat)) {
    oled.print(d.harorat, 1);
    oled.print((char)247);   // ° belgisi
    oled.print("C");
  } else {
    oled.print("-- (xato)");
  }

  // Namlik
  oled.setCursor(0, 24);
  oled.print("H: ");
  if (!isnan(d.namlik)) {
    oled.print(d.namlik, 0);
    oled.print("%");
  } else {
    oled.print("-- (xato)");
  }

  // Wi-Fi holati
  oled.setCursor(0, 35);
  oled.print("WiFi: ");
  oled.print(wifi_ulangan ? "Ulangan" : "Yo'q");

  oled.drawLine(0, 45, 127, 45, SSD1306_WHITE);

  // Umumiy holat
  oled.setCursor(0, 49);
  oled.print("Holat: ");
  oled.print(holat_aniqlash(d));

  // Sahifa ko'rsatkichi
  oled.setCursor(104, 57);
  oled.print("1/3");

  oled.display();
}

// ═══════════════════════════════════════════════════════════════
// OLED SAHIFA 2 — GAZ SENSORLARI
//
//  ┌──────────────┐
//  │ GAZ HOLATI   │
//  │──────────────│
//  │ MQ135: Toza  │
//  │ MQ2:   Toza  │
//  │ MQ7:   Toza  │
//  │──────────────│
//  │ Xavf yo'q    │
//  └──────────────┘
// ═══════════════════════════════════════════════════════════════
void oled_sahifa2(const SensorData& d) {
  oled.clearDisplay();
  oled.setTextColor(SSD1306_WHITE);
  oled.setTextSize(1);

  // Sarlavha
  oled.setCursor(22, 0);
  oled.println("GAZ HOLATI");
  oled.drawLine(0, 9, 127, 9, SSD1306_WHITE);

  // MQ-135
  oled.setCursor(0, 13);
  oled.print("MQ135: ");
  if (ENABLE_MQ135 && d.mq135 >= 0)
    oled.print(d.mq135 == 1 ? "Toza" : "!XAVF!");
  else
    oled.print("--");

  // MQ-2
  oled.setCursor(0, 24);
  oled.print("MQ2:   ");
  if (ENABLE_MQ2 && d.mq2 >= 0)
    oled.print(d.mq2 == 1 ? "Toza" : "!XAVF!");
  else
    oled.print("--");

  // MQ-7
  oled.setCursor(0, 35);
  oled.print("MQ7:   ");
  if (ENABLE_MQ7 && d.mq7 >= 0)
    oled.print(d.mq7 == 1 ? "Toza" : "!XAVF!");
  else
    oled.print("--");

  oled.drawLine(0, 45, 127, 45, SSD1306_WHITE);

  // Xulosa
  oled.setCursor(0, 49);
  bool xavf_bor = (ENABLE_MQ135 && d.mq135 == 0) ||
                  (ENABLE_MQ2   && d.mq2   == 0) ||
                  (ENABLE_MQ7   && d.mq7   == 0);
  oled.print(xavf_bor ? "!! Xavf bor !!" : "Xavf yo'q");

  // Sahifa ko'rsatkichi
  oled.setCursor(104, 57);
  oled.print("2/3");

  oled.display();
}

// ═══════════════════════════════════════════════════════════════
// OLED SAHIFA 3 — SERVER HOLATI
//
//  ┌──────────────┐
//  │ SERVER       │
//  │──────────────│
//  │ IP: ...136   │
//  │ Yuborildi: 5 │
//  │ Oxirgi: 14:30│
//  │──────────────│
//  │ Ulangan      │
//  └──────────────┘
// ═══════════════════════════════════════════════════════════════
void oled_sahifa3() {
  oled.clearDisplay();
  oled.setTextColor(SSD1306_WHITE);
  oled.setTextSize(1);

  // Sarlavha
  oled.setCursor(34, 0);
  oled.println("SERVER");
  oled.drawLine(0, 9, 127, 9, SSD1306_WHITE);

  // Server IP (oxirgi oktet)
  oled.setCursor(0, 13);
  oled.print("IP: ...136");

  // Yuborildi soni
  oled.setCursor(0, 24);
  oled.print("Yuborildi: ");
  oled.print(yuborish_soni);

  // Oxirgi yuborish vaqti
  oled.setCursor(0, 35);
  oled.print("Oxirgi: ");
  oled.print(oxirgi_vaqt);

  oled.drawLine(0, 45, 127, 45, SSD1306_WHITE);

  // Ulanish holati
  oled.setCursor(0, 49);
  if (wifi_ulangan && server_ulangan)
    oled.print("Ulangan");
  else if (wifi_ulangan)
    oled.print("WiFi bor, server?");
  else
    oled.print("WiFi yo'q");

  // Sahifa ko'rsatkichi
  oled.setCursor(104, 57);
  oled.print("3/3");

  oled.display();
}

// ═══════════════════════════════════════════════════════════════
// OLED YANGILASH — har 5 sekundda sahifa almashinadi
// ═══════════════════════════════════════════════════════════════
void oled_yangilash(const SensorData& d) {
  if (!ENABLE_OLED) return;

  unsigned long hozir = millis();

  // Sahifani almashtirish
  if (hozir - oxirgi_sahifa_alm >= SAHIFA_INTERVAL) {
    oxirgi_sahifa_alm = hozir;
    joriy_sahifa = (joriy_sahifa + 1) % 3;
  }

  // Ekranni chizish (har 1 sekundda yangilanadi)
  if (hozir - oxirgi_oled_draw >= 1000) {
    oxirgi_oled_draw = hozir;
    switch (joriy_sahifa) {
      case 0: oled_sahifa1(d); break;
      case 1: oled_sahifa2(d); break;
      case 2: oled_sahifa3();  break;
    }
  }
}

// ═══════════════════════════════════════════════════════════════
// SETUP — bir marta ishga tushadi
// ═══════════════════════════════════════════════════════════════
void setup() {
  Serial.begin(115200);
  delay(500);

  // Kirish banneri
  Serial.println("\n╔════════════════════════════════════════════════╗");
  Serial.println("║   Havo Sifati Monitoringi — ESP32 v3.0        ║");
  Serial.println("║   Diplom loyihasi, 2025-2026                   ║");
  Serial.println("╠════════════════════════════════════════════════╣");
  Serial.println("║   MQ-135 → GPIO 23 | MQ-2 → GPIO 5            ║");
  Serial.println("║   MQ-7   → GPIO 19 | DHT22 → GPIO 4           ║");
  Serial.println("║   OLED   → SDA=21, SCL=22 (I2C, 0x3C)         ║");
  Serial.println("╚════════════════════════════════════════════════╝\n");

  // ─── OLED ni ishga tushirish ───────────────────────────────
  if (ENABLE_OLED) {
    Wire.begin(21, 22);   // SDA=21, SCL=22
    if (!oled.begin(SSD1306_SWITCHCAPVCC, OLED_ADDRESS)) {
      Serial.println("❌ OLED topilmadi! I2C manzilni tekshiring (0x3C yoki 0x3D)");
    } else {
      Serial.println("✅ OLED ishga tushdi (128x64, I2C 0x3C)");
      oled.clearDisplay();
      oled.setTextSize(1);
      oled.setTextColor(SSD1306_WHITE);
      oled.setCursor(8, 10);
      oled.println("Havo Monitoringi");
      oled.setCursor(10, 25);
      oled.println("Ishga tushmoqda...");
      oled.setCursor(20, 45);
      oled.println("Diplom 2025-2026");
      oled.display();
      delay(2000);
    }
  }

  // ─── Sensor pinlarini sozlash ──────────────────────────────
  Serial.println("⚙️  Sensorlar sozlanmoqda...");

  if (ENABLE_MQ135) {
    pinMode(MQ135_PIN, INPUT);
    Serial.println("   ✅ MQ-135 — GPIO 23 (CO₂/NH₃/Benzol)");
  }
  if (ENABLE_MQ2) {
    pinMode(MQ2_PIN, INPUT);
    Serial.println("   ✅ MQ-2   — GPIO 5  (Metan/LPG/Tutun)");
  }
  if (ENABLE_MQ7) {
    pinMode(MQ7_PIN, INPUT);
    Serial.println("   ✅ MQ-7   — GPIO 19 (Uglerod oksidi)");
  }
  if (ENABLE_DHT22) {
    dht.begin();
    Serial.println("   ✅ DHT22  — GPIO 4  (Harorat/Namlik)");
  }

  // Kelajakdagi sensorlar uchun joy (hozir izoh):
  // if (ENABLE_BMP280) {
  //   if (bmp.begin(BMP280_ADDRESS))
  //     Serial.println("   ✅ BMP280 — I2C 0x76 (Harorat/Bosim)");
  //   else
  //     Serial.println("   ❌ BMP280 topilmadi!");
  // }
  // if (ENABLE_SDS011) {
  //   sdsSerial.begin(9600);
  //   Serial.println("   ✅ SDS011 — UART RX=16, TX=17 (PM2.5/PM10)");
  // }

  // ─── Wi-Fi (oflayn rejim qo'llab-quvvatlanadi) ────────────
  wifi_urinib_kor();

  // ─── Tayyor xabari ────────────────────────────────────────
  Serial.println("\n📋 Konfiguratsiya:");
  Serial.print("   🌐 Server     : "); Serial.println(SERVER_URL);
  Serial.print("   📟 Qurilma ID : "); Serial.println(DEVICE_ID);
  Serial.print("   ⏱️  Interval   : "); Serial.print(YUBORISH_INTERVALI / 1000); Serial.println(" sekund");
  Serial.println("\n✨ Qurilma tayyor! Sensorlar o'qilmoqda...\n");

  // Birinchi o'lchovni darhol boshlash
  oxirgi_yuborish   = millis() - YUBORISH_INTERVALI;
  oxirgi_sahifa_alm = millis();
  oxirgi_oled_draw  = millis();
}

// ═══════════════════════════════════════════════════════════════
// LOOP — doimo takrorlanadi
// ═══════════════════════════════════════════════════════════════
void loop() {
  unsigned long hozir = millis();

  // ─── Belgilangan vaqt o'tganda: o'qi va yubor ─────────────
  if (hozir - oxirgi_yuborish >= YUBORISH_INTERVALI) {
    oxirgi_yuborish = hozir;

    // Barcha yoqilgan sensorlardan o'qish
    joriy_data = sensorlar_oqi();

    // Serial Monitor ga batafsil log
    serial_log(joriy_data);

    // Wi-Fi bor bo'lsa — serverga yuborish
    if (WiFi.status() == WL_CONNECTED) {
      bool natija = serverga_yubor(joriy_data);
      if (natija) {
        Serial.print("⏳ Keyingi o'lchov ");
        Serial.print(YUBORISH_INTERVALI / 1000);
        Serial.println(" sekunddan so'ng\n");
      } else {
        Serial.println("⚠️  Yuborishda muammo — keyingi urinishda qayta yuboriladi\n");
      }
    } else {
      Serial.println("📵 WiFi yo'q — ma'lumot faqat OLED va Serial ga chiqarildi\n");
    }
  }

  // ─── Wi-Fi uzilishini kuzatish va qayta ulanish ────────────
  if (WiFi.status() != WL_CONNECTED) {
    if (wifi_ulangan) {
      // Yangi uzilish — hozir qayta urinib ko'ramiz
      wifi_ulangan = false;
      server_ulangan = false;
      Serial.println("⚠️  Wi-Fi uzildi!");
      oxirgi_qayta_ulan = hozir - QAYTA_ULANISH_MS;  // darhol urinish
    }
    // Belgilangan interval o'tganda qayta ulanishga harakat
    if (hozir - oxirgi_qayta_ulan >= QAYTA_ULANISH_MS) {
      oxirgi_qayta_ulan = hozir;
      wifi_urinib_kor();
    }
  } else {
    wifi_ulangan = true;
  }

  // ─── OLED ekranini yangilash (har 1s, sahifa har 5s) ───────
  if (ENABLE_OLED) {
    oled_yangilash(joriy_data);
  }

  delay(100);    // Protsessor yukini kamaytirish
}
