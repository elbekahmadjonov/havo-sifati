/*
  Havo Sifati Monitoringi — ESP32 Arduino kodi
  Diplom ishi: "Havo sifatining bashoratli monitoringi uchun aqlli qurilma"

  Ulanish:
    MQ-135 DO → GPIO 23
    MQ-2   DO → GPIO 22

  Ishlash tartibi:
    1. Wi-Fi ga ulanadi
    2. Har 30 sekundda sensorlarni o'qiydi
    3. HTTP POST orqali serverga yuboradi
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ─────────────────────────────────────────────
// O'ZGARTIRISH KERAK BO'LGAN SOZLAMALAR
// ─────────────────────────────────────────────

// Wi-Fi ma'lumotlari
const char* WIFI_SSID     = "SIZNING_WIFI_NOMI";
const char* WIFI_PAROL    = "SIZNING_WIFI_PAROLI";

// Server manzili — kompyuteringizning lokal IP manzili
// (cmd > ipconfig > IPv4 Address ni ko'ring)
const char* SERVER_URL    = "http://192.168.1.100:8000/sensor";

// ─────────────────────────────────────────────
// GPIO pinlari
// ─────────────────────────────────────────────
const int MQ135_PIN = 23;   // MQ-135 raqamli chiqishi (DO)
const int MQ2_PIN   = 22;   // MQ-2 raqamli chiqishi (DO)

// ─────────────────────────────────────────────
// Vaqt sozlamalari
// ─────────────────────────────────────────────
const unsigned long YUBORISH_INTERVAL = 30000;   // 30 sekund (millisekund)
unsigned long oxirgi_yuborish = 0;

// ─────────────────────────────────────────────
// Wi-Fi ga ulanish
// ─────────────────────────────────────────────
void wifiGaUlan() {
  Serial.print("📡 Wi-Fi ga ulanilmoqda: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PAROL);

  int urinish = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    urinish++;
    if (urinish > 40) {
      // 20 sekunddan keyin qayta urinish
      Serial.println("\n⚠ Wi-Fi ga ulanib bo'lmadi! Qayta urinilmoqda...");
      WiFi.disconnect();
      delay(1000);
      WiFi.begin(WIFI_SSID, WIFI_PAROL);
      urinish = 0;
    }
  }

  Serial.println("\n✅ Wi-Fi ga ulandi!");
  Serial.print("   IP manzili: ");
  Serial.println(WiFi.localIP());
  Serial.print("   Signal kuchi: ");
  Serial.print(WiFi.RSSI());
  Serial.println(" dBm");
}

// ─────────────────────────────────────────────
// Sensorlarni o'qish
// ─────────────────────────────────────────────
struct SensorQiymat {
  int mq135;   // 1=toza, 0=gaz aniqlandi
  int mq2;     // 1=toza, 0=gaz aniqlandi
};

SensorQiymat sensorlarniOqi() {
  SensorQiymat q;

  // MQ sensor DO (Digital Output):
  //   HIGH (1) → sensor tahdid aniqlamadi (toza havo)
  //   LOW  (0) → sensor gaz aniqladi (xavf bor)
  q.mq135 = digitalRead(MQ135_PIN);
  q.mq2   = digitalRead(MQ2_PIN);

  return q;
}

// ─────────────────────────────────────────────
// Serverga HTTP POST yuborish
// ─────────────────────────────────────────────
bool serveraYubor(SensorQiymat q) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠ Wi-Fi ulanishi yo'q! Qayta ulanilmoqda...");
    wifiGaUlan();
    return false;
  }

  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");

  // JSON tuzish
  StaticJsonDocument<128> doc;
  doc["mq135"] = q.mq135;
  doc["mq2"]   = q.mq2;

  String json;
  serializeJson(doc, json);

  Serial.print("📤 Yuborilmoqda: ");
  Serial.println(json);

  int httpKod = http.POST(json);

  if (httpKod == HTTP_CODE_OK) {
    String javob = http.getString();
    Serial.print("✅ Server javobi (");
    Serial.print(httpKod);
    Serial.print("): ");
    Serial.println(javob);
    http.end();
    return true;
  } else if (httpKod > 0) {
    Serial.print("⚠ HTTP xato kodi: ");
    Serial.println(httpKod);
  } else {
    Serial.print("❌ Ulanish xatosi: ");
    Serial.println(http.errorToString(httpKod));
  }

  http.end();
  return false;
}

// ─────────────────────────────────────────────
// Sensor holatini chiroyli chiqarish
// ─────────────────────────────────────────────
void holatChiqar(SensorQiymat q) {
  Serial.println("─────────────────────────────────────");
  Serial.print("🔬 MQ-135 (CO2/NH3/Benzol): ");
  if (q.mq135 == 1) Serial.println("✅ TOZA");
  else               Serial.println("🚨 GAZ ANIQLANDI!");

  Serial.print("🔥 MQ-2   (LPG/Propan):    ");
  if (q.mq2 == 1) Serial.println("✅ TOZA");
  else             Serial.println("🚨 GAZ ANIQLANDI!");
  Serial.println("─────────────────────────────────────");
}

// ─────────────────────────────────────────────
// Setup — bir marta ishga tushadi
// ─────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("\n╔══════════════════════════════════════╗");
  Serial.println("║  Havo Sifati Monitoringi — ESP32    ║");
  Serial.println("║  Diplom loyihasi, 2025              ║");
  Serial.println("╚══════════════════════════════════════╝");

  // GPIO pinlarini kirish sifatida sozlash
  pinMode(MQ135_PIN, INPUT);
  pinMode(MQ2_PIN,   INPUT);

  Serial.println("⚙ Sensor pinlari sozlandi:");
  Serial.print("  MQ-135 → GPIO "); Serial.println(MQ135_PIN);
  Serial.print("  MQ-2   → GPIO "); Serial.println(MQ2_PIN);

  // Wi-Fi ga ulanish
  wifiGaUlan();

  // Birinchi o'lchov darhol yuborilsin
  oxirgi_yuborish = millis() - YUBORISH_INTERVAL;

  Serial.print("⏱ Ma'lumot yuborish intervali: ");
  Serial.print(YUBORISH_INTERVAL / 1000);
  Serial.println(" sekund");
  Serial.println("✨ Qurilma ishga tushdi!\n");
}

// ─────────────────────────────────────────────
// Loop — doimo takrorlanadi
// ─────────────────────────────────────────────
void loop() {
  unsigned long hozir = millis();

  // Belgilangan vaqt o'tganda ma'lumot yuborish
  if (hozir - oxirgi_yuborish >= YUBORISH_INTERVAL) {
    oxirgi_yuborish = hozir;

    // Sensorlarni o'qish
    SensorQiymat q = sensorlarniOqi();

    // Serial Monitor ga chiqarish
    holatChiqar(q);

    // Serverga yuborish
    bool muvaffaqiyat = serveraYubor(q);
    if (!muvaffaqiyat) {
      Serial.println("⚠ Keyingi urinishda qayta yuboriladi.");
    }

    // Qolgan vaqtni ko'rsatish
    Serial.print("⏳ Keyingi o'lchov: ");
    Serial.print(YUBORISH_INTERVAL / 1000);
    Serial.println(" sekunddan so'ng\n");
  }

  // Wi-Fi aloqasini kuzatish
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠ Wi-Fi uzildi! Qayta ulanilmoqda...");
    wifiGaUlan();
  }

  delay(100);   // protsessor yukini kamaytirish
}
