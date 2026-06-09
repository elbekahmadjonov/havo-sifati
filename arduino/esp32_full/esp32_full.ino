

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#include <Adafruit_BMP280.h>

const char* WIFI_SSID     = "esp32";       
const char* WIFI_PASSWORD = "12123434";     

const char* SERVER_URL    = "http://157.173.114.153/api/sensor";

const char* DEVICE_ID     = "esp32_001";

const unsigned long YUBORISH_INTERVALI = 10000;   

const unsigned long SAHIFA_INTERVAL    = 5000;    

const unsigned long QAYTA_ULANISH_MS   = 30000;   

const bool ENABLE_MQ135  = true;    
const bool ENABLE_MQ2    = true;    
const bool ENABLE_MQ7    = true;    
const bool ENABLE_DHT22  = true;    
const bool ENABLE_OLED   = true;    

const bool ENABLE_BMP280  = true;   
const bool ENABLE_PMS5003 = true;   

const int MQ135_PIN = 5;
const int MQ2_PIN   = 4;
const int MQ7_PIN   = 19;
const int DHT22_PIN = 23;

const int PMS5003_RX   = 16;  
const int PMS5003_TX   = 17;  
#define   DHT_TYPE  DHT22    

#define OLED_WIDTH   128     
#define OLED_HEIGHT  64      
#define OLED_ADDRESS 0x3C    
#define OLED_RESET   -1      

#define BMP280_ADDRESS 0x76   

DHT           dht(DHT22_PIN, DHT_TYPE);
Adafruit_SSD1306 oled(OLED_WIDTH, OLED_HEIGHT, &Wire, OLED_RESET);

Adafruit_BMP280  bmp;           
HardwareSerial   pmsSerial(2);  

unsigned long oxirgi_yuborish    = 0;       
unsigned long oxirgi_sahifa_alm  = 0;       
unsigned long oxirgi_oled_draw   = 0;       
unsigned long oxirgi_qayta_ulan  = 0;       

int  joriy_sahifa    = 0;       
int  yuborish_soni   = 0;       
int  xato_soni       = 0;       
bool server_ulangan  = false;   
bool wifi_ulangan    = false;   
char oxirgi_vaqt[9]  = "--:--"; 

struct SensorData {
  int   mq135   = -1;
  int   mq2     = -1;
  int   mq7     = -1;
  float harorat = NAN;
  float namlik  = NAN;
  float bosim   = NAN;
  float pm25    = NAN;
  float pm10    = NAN;
};

SensorData joriy_data;      

int   g_pm25 = -1;             
int   g_pm10 = -1;
unsigned long g_pms_vaqt = 0;  

void vaqt_yangilash() {
  unsigned long jami_sekund = millis() / 1000;
  int minut  = (jami_sekund / 60) % 60;
  int sekund = jami_sekund % 60;
  snprintf(oxirgi_vaqt, sizeof(oxirgi_vaqt), "%02d:%02d", minut, sekund);
}

const char* holat_aniqlash(const SensorData& d) {
  if ((ENABLE_MQ135 && d.mq135 == 0) ||
      (ENABLE_MQ2   && d.mq2   == 0) ||
      (ENABLE_MQ7   && d.mq7   == 0)) {
    return "XAVFLI";
  }
  return "YAXSHI";
}

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

    if (++urinish >= 40) {   
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

void pms_loop_oqi() {
  if (!ENABLE_PMS5003) return;
  if (millis() < 30000)  return;   
  if (pmsSerial.available() < 32) return;   

  uint8_t buf[32];

  while (pmsSerial.available() >= 32) {
    if (pmsSerial.read() != 0x42) continue;
    if (!pmsSerial.available() || pmsSerial.peek() != 0x4D) continue;

    buf[0] = 0x42;
    if (pmsSerial.readBytes(&buf[1], 31) != 31) return;

    
    uint16_t cs = 0;
    for (int i = 0; i < 30; i++) cs += buf[i];
    if (cs != (((uint16_t)buf[30] << 8) | buf[31])) return;

    int v25 = (int)(((uint16_t)buf[6] << 8) | buf[7]);
    int v10 = (int)(((uint16_t)buf[8] << 8) | buf[9]);

    
    if (v25 > 1000 || v10 > 2000) return;

    g_pm25      = v25;
    g_pm10      = v10;
    g_pms_vaqt  = millis();
    return;   
  }
}

SensorData sensorlar_oqi() {
  SensorData d;

  
  if (ENABLE_MQ135) { d.mq135 = digitalRead(MQ135_PIN); }
  if (ENABLE_MQ2)   { d.mq2   = digitalRead(MQ2_PIN);   }
  if (ENABLE_MQ7)   { d.mq7   = digitalRead(MQ7_PIN);   }

  
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

  
  if (ENABLE_BMP280) {
    
    float bosim_pa = bmp.readPressure();
    if (bosim_pa > 0 && !isnan(bosim_pa)) {
      d.bosim = bosim_pa / 100.0F;
    } else {
      Serial.println("⚠️  BMP280 bosim o'qilmadi — null yuboriladi");
    }
  }

  
  
  
  if (ENABLE_PMS5003) {
    if (millis() < 30000) {
      Serial.print("   PMS5003 isinmoqda: ");
      Serial.print(millis() / 1000);
      Serial.println("s / 30s");
    } else if (g_pm25 >= 0) {
      d.pm25 = (float)g_pm25;
      d.pm10 = (float)g_pm10;
      Serial.print("   PM2.5: "); Serial.print(g_pm25); Serial.println(" ug/m3");
      Serial.print("   PM10:  "); Serial.print(g_pm10); Serial.println(" ug/m3");
    } else {
      Serial.println("   PMS5003: hali o'qilmagan — null yuboriladi");
    }
  }

  
  
  
  
  
  
  
  
  

  return d;
}

bool serverga_yubor(const SensorData& d) {
  if (WiFi.status() != WL_CONNECTED) {
    wifi_ulangan = false;
    Serial.println("📵 Wi-Fi yo'q — yuborilmaydi, sensorlar o'qishda davom etadi");
    return false;
  }

  
  StaticJsonDocument<384> doc;
  doc["device_id"] = DEVICE_ID;

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

  
  if (!isnan(d.bosim))
    doc["bosim"] = (float)round(d.bosim * 10) / 10.0f;
  else
    doc["bosim"] = nullptr;

  
  if (!isnan(d.pm25)) doc["pm25"] = (float)round(d.pm25 * 10) / 10.0f; else doc["pm25"] = nullptr;
  if (!isnan(d.pm10)) doc["pm10"] = (float)round(d.pm10 * 10) / 10.0f; else doc["pm10"] = nullptr;

  String json;
  serializeJson(doc, json);

  Serial.print("📤 Yuborilmoqda → ");
  Serial.println(SERVER_URL);
  Serial.print("   Kalit: "); Serial.println(json);
  Serial.print("   WiFi IP : "); Serial.println(WiFi.localIP());
  Serial.print("   RSSI    : "); Serial.print(WiFi.RSSI()); Serial.println(" dBm");

  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(10000);  

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
    Serial.print("⚠️  HTTP xato kodi: "); Serial.println(kod);
    Serial.print("   Server javobi : "); Serial.println(http.getString());
    Serial.println("   SERVER_URL ni tekshiring: " + String(SERVER_URL));
  } else {
    Serial.print("❌ Ulanish xatosi ("); Serial.print(kod); Serial.print("): ");
    Serial.println(http.errorToString(kod));
    Serial.println("   Server ishlamayapti yoki IP noto'g'ri: " + String(SERVER_URL));
  }

  http.end();
  xato_soni++;
  server_ulangan = false;
  return false;
}

void serial_log(const SensorData& d) {
  Serial.println("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  Serial.print("📊 O'lchov #");
  Serial.print(yuborish_soni + 1);
  Serial.print("  |  Ishlash vaqti: ");
  Serial.print(millis() / 1000);
  Serial.println("s");
  Serial.println("──────────────────────────────────────────────");

  
  if (ENABLE_MQ135) {
    Serial.print("🏭 MQ-135 : ");
    Serial.println(d.mq135 == 1 ? "TOZA" : "GAZ!");
  }
  if (ENABLE_MQ2) {
    Serial.print("🔥 MQ-2   : ");
    Serial.println(d.mq2 == 1 ? "TOZA" : "GAZ!");
  }
  if (ENABLE_MQ7) {
    Serial.print("💨 MQ-7   : ");
    Serial.println(d.mq7 == 1 ? "TOZA" : "GAZ!");
  }

  Serial.println("──────────────────────────────────────────────");

  
  if (ENABLE_DHT22) {
    Serial.print("🌡️  Harorat  : ");
    if (!isnan(d.harorat)) { Serial.print(d.harorat, 1); Serial.println(" °C"); }
    else                    Serial.println("❌ null (DHT22 xato)");

    Serial.print("💧 Namlik   : ");
    if (!isnan(d.namlik))  { Serial.print(d.namlik, 1); Serial.println(" %"); }
    else                    Serial.println("❌ null (DHT22 xato)");
  }

  
  if (!isnan(d.bosim)) {
    Serial.print("🌬️  Bosim    : "); Serial.print(d.bosim, 1); Serial.println(" hPa");
  }

  
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

void oled_sahifa1(const SensorData& d) {
  oled.clearDisplay();
  oled.setTextColor(SSD1306_WHITE);
  oled.setTextSize(1);

  
  oled.setCursor(16, 0);
  oled.println("HAVO SIFATI");
  oled.drawLine(0, 9, 127, 9, SSD1306_WHITE);

  
  oled.setCursor(0, 13);
  oled.print("T: ");
  if (!isnan(d.harorat)) {
    oled.print(d.harorat, 1);
    oled.print((char)247);   
    oled.print("C");
  } else {
    oled.print("-- (xato)");
  }

  
  oled.setCursor(0, 24);
  oled.print("H: ");
  if (!isnan(d.namlik)) {
    oled.print(d.namlik, 0);
    oled.print("%");
  } else {
    oled.print("-- (xato)");
  }

  
  oled.setCursor(0, 35);
  oled.print("WiFi: ");
  oled.print(wifi_ulangan ? "Ulangan" : "Yo'q");

  oled.drawLine(0, 45, 127, 45, SSD1306_WHITE);

  
  oled.setCursor(0, 49);
  oled.print("Holat: ");
  oled.print(holat_aniqlash(d));

  
  oled.setCursor(104, 57);
  oled.print("1/3");

  oled.display();
}

void oled_sahifa2(const SensorData& d) {
  oled.clearDisplay();
  oled.setTextColor(SSD1306_WHITE);
  oled.setTextSize(1);

  
  oled.setCursor(22, 0);
  oled.println("GAZ HOLATI");
  oled.drawLine(0, 9, 127, 9, SSD1306_WHITE);

  
  oled.setCursor(0, 13);
  oled.print("MQ135: ");
  if (ENABLE_MQ135 && d.mq135 >= 0)
    oled.print(d.mq135 == 1 ? "Toza" : "!XAVF!");
  else
    oled.print("--");

  
  oled.setCursor(0, 24);
  oled.print("MQ2:   ");
  if (ENABLE_MQ2 && d.mq2 >= 0)
    oled.print(d.mq2 == 1 ? "Toza" : "!XAVF!");
  else
    oled.print("--");

  
  oled.setCursor(0, 35);
  oled.print("MQ7:   ");
  if (ENABLE_MQ7 && d.mq7 >= 0)
    oled.print(d.mq7 == 1 ? "Toza" : "!XAVF!");
  else
    oled.print("--");

  oled.drawLine(0, 45, 127, 45, SSD1306_WHITE);

  
  oled.setCursor(0, 49);
  bool xavf_bor = (ENABLE_MQ135 && d.mq135 == 0) ||
                  (ENABLE_MQ2   && d.mq2   == 0) ||
                  (ENABLE_MQ7   && d.mq7   == 0);
  oled.print(xavf_bor ? "!! Xavf bor !!" : "Xavf yo'q");

  
  oled.setCursor(104, 57);
  oled.print("2/3");

  oled.display();
}

void oled_sahifa3(const SensorData& d) {
  oled.clearDisplay();
  oled.setTextColor(SSD1306_WHITE);
  oled.setTextSize(1);

  
  oled.setCursor(22, 0);
  oled.println("BOSIM/SERVER");
  oled.drawLine(0, 9, 127, 9, SSD1306_WHITE);

  
  oled.setCursor(0, 13);
  oled.print("Bosim: ");
  if (!isnan(d.bosim)) {
    oled.print(d.bosim, 1);
    oled.print(" hPa");
  } else {
    oled.print("-- (ulanmagan)");
  }

  
  oled.setCursor(0, 24);
  oled.print("Yuborildi: ");
  oled.print(yuborish_soni);

  
  oled.setCursor(0, 35);
  oled.print("Oxirgi: ");
  oled.print(oxirgi_vaqt);

  oled.drawLine(0, 45, 127, 45, SSD1306_WHITE);

  
  oled.setCursor(0, 49);
  if (wifi_ulangan && server_ulangan)
    oled.print("Ulangan");
  else if (wifi_ulangan)
    oled.print("WiFi bor, server?");
  else
    oled.print("WiFi yo'q");

  
  oled.setCursor(104, 57);
  oled.print("3/3");

  oled.display();
}

void oled_sahifa4(const SensorData& d) {
  oled.clearDisplay();
  oled.setTextColor(SSD1306_WHITE);
  oled.setTextSize(1);

  oled.setCursor(25, 0);
  oled.println("CHANG (PMS5003)");
  oled.drawLine(0, 9, 127, 9, SSD1306_WHITE);

  oled.setCursor(0, 13);
  oled.print("PM2.5: ");
  if (!isnan(d.pm25)) { oled.print(d.pm25, 1); oled.println(" ug/m3"); }
  else                 { oled.println("-- (ulanmagan)"); }

  oled.setCursor(0, 24);
  oled.print("PM10:  ");
  if (!isnan(d.pm10)) { oled.print(d.pm10, 1); oled.println(" ug/m3"); }
  else                 { oled.println("-- (ulanmagan)"); }

  oled.setCursor(0, 35);
  if (!isnan(d.pm25)) {
    oled.print("Holat: ");
    if      (d.pm25 <= 12.0)  oled.print("Yaxshi");
    else if (d.pm25 <= 35.4)  oled.print("Qoniqarli");
    else if (d.pm25 <= 55.4)  oled.print("Sezgir");
    else                      oled.print("! Iflos !");
  }

  oled.drawLine(0, 45, 127, 45, SSD1306_WHITE);

  oled.setCursor(0, 49);
  if (!isnan(d.pm25) && d.pm25 > 35.4)
    oled.print("!! Chang ko'p !!");
  else
    oled.print("Chang normal");

  oled.setCursor(98, 57);
  oled.print("4/4");

  oled.display();
}

void oled_yangilash(const SensorData& d) {
  if (!ENABLE_OLED) return;

  unsigned long hozir = millis();

  if (hozir - oxirgi_sahifa_alm >= SAHIFA_INTERVAL) {
    oxirgi_sahifa_alm = hozir;
    joriy_sahifa = (joriy_sahifa + 1) % 4;  
  }

  if (hozir - oxirgi_oled_draw >= 1000) {
    oxirgi_oled_draw = hozir;
    switch (joriy_sahifa) {
      case 0: oled_sahifa1(d); break;
      case 1: oled_sahifa2(d); break;
      case 2: oled_sahifa3(d); break;
      case 3: oled_sahifa4(d); break;
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(500);

  
  Serial.println("\n╔════════════════════════════════════════════════╗");
  Serial.println("║   Havo Sifati Monitoringi — ESP32 v3.0        ║");
  Serial.println("║   Diplom loyihasi, 2025-2026                   ║");
  Serial.println("╠════════════════════════════════════════════════╣");
  Serial.println("║   MQ-135 DO:GPIO4  | MQ-2 DO:GPIO5  | MQ-7:GPIO19 ║");
  Serial.println("║   DHT22: GPIO23  | OLED SDA=21,SCL=22 (0x3C)  ║");
  Serial.println("║   BMP280 (0x76)  | PMS5003 UART2 RX=16,TX=17  ║");
  Serial.println("╚════════════════════════════════════════════════╝\n");

  
  if (ENABLE_OLED) {
    Wire.begin(21, 22);   
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

  
  Serial.println("⚙️  Sensorlar sozlanmoqda...");

  
  if (ENABLE_MQ135) {
    pinMode(MQ135_PIN, INPUT_PULLUP);
    Serial.println("   ✅ MQ-135 — GPIO 4  (CO₂/NH₃/Benzol, INPUT_PULLUP)");
  }
  if (ENABLE_MQ2) {
    pinMode(MQ2_PIN, INPUT_PULLUP);
    Serial.println("   ✅ MQ-2   — GPIO 5  (Metan/LPG/Tutun, INPUT_PULLUP)");
  }
  if (ENABLE_MQ7) {
    pinMode(MQ7_PIN, INPUT_PULLUP);
    Serial.println("   ✅ MQ-7   — GPIO 19 (Uglerod oksidi, INPUT_PULLUP)");
  }
  if (ENABLE_DHT22) {
    dht.begin();
    Serial.println("   ✅ DHT22  — GPIO 23 (Harorat/Namlik)");
  }

  
  if (ENABLE_PMS5003) {
    pmsSerial.begin(9600, SERIAL_8N1, PMS5003_RX, PMS5003_TX);
    Serial.println("   PMS5003 -- UART2 RX=16, TX=17 (30s isinish kerak)");
  }

  
  if (ENABLE_BMP280) {
    if (bmp.begin(BMP280_ADDRESS)) {
      Serial.println("   ✅ BMP280 — I2C 0x76 (Bosim sensori, hPa)");
    } else {
      
      Serial.println("   ⚠️  BMP280 topilmadi! SDA=21, SCL=22, manzil 0x76 tekshiring");
      Serial.println("       Tizim davom etadi — bosim null bo'ladi");
    }
  }
  
  
  
  

  
  wifi_urinib_kor();

  
  Serial.println("\n📋 Konfiguratsiya:");
  Serial.print("   🌐 Server     : "); Serial.println(SERVER_URL);
  Serial.print("   📟 Qurilma ID : "); Serial.println(DEVICE_ID);
  Serial.print("   ⏱️  Interval   : "); Serial.print(YUBORISH_INTERVALI / 1000); Serial.println(" sekund");
  Serial.println("\n✨ Qurilma tayyor! Sensorlar o'qilmoqda...\n");

  
  oxirgi_yuborish   = millis() - YUBORISH_INTERVALI;
  oxirgi_sahifa_alm = millis();
  oxirgi_oled_draw  = millis();
}

void loop() {
  unsigned long hozir = millis();

  
  if (hozir - oxirgi_yuborish >= YUBORISH_INTERVALI) {
    oxirgi_yuborish = hozir;

    
    joriy_data = sensorlar_oqi();

    
    serial_log(joriy_data);

    
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

  
  if (WiFi.status() != WL_CONNECTED) {
    if (wifi_ulangan) {
      
      wifi_ulangan = false;
      server_ulangan = false;
      Serial.println("⚠️  Wi-Fi uzildi!");
      oxirgi_qayta_ulan = hozir - QAYTA_ULANISH_MS;  
    }
    
    if (hozir - oxirgi_qayta_ulan >= QAYTA_ULANISH_MS) {
      oxirgi_qayta_ulan = hozir;
      wifi_urinib_kor();
    }
  } else {
    wifi_ulangan = true;
  }

  
  pms_loop_oqi();

  
  if (ENABLE_OLED) {
    oled_yangilash(joriy_data);
  }

  delay(100);    
}
