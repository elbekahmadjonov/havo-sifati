<<<<<<< HEAD
# Havo Sifati Monitoringi v2.0

**Diplom ishi:** "Havo sifatining bashoratli monitoringi uchun aqlli qurilma va dasturiy ta'minot"

---

## Tizim arxitekturasi

```
┌─────────────────┐    HTTP POST     ┌──────────────────────┐
│   ESP32 + MQ    │ ──────────────►  │  FastAPI Server      │
│   Sensorlar     │  /api/sensor     │  (Python 3.14)       │
└─────────────────┘                  └──────────┬───────────┘
                                                │
                              ┌─────────────────┼──────────────────┐
                              │                 │                   │
                    ┌─────────▼──────┐  ┌──────▼──────┐  ┌───────▼───────┐
                    │  SQLite DB     │  │  AQI Modul  │  │  ML Bashorat  │
                    │  havo_data.db  │  │  (EPA std.) │  │  (Placeholder)│
                    └────────────────┘  └─────────────┘  └───────────────┘
                                                │
                                    ┌───────────▼───────────┐
                                    │  Web Dashboard        │
                                    │  (Brauzer, AJAX)      │
                                    └───────────────────────┘
```

## Fayl tuzilmasi

```
diplom_server/
├── server.py              ← FastAPI asosiy server (9 ta endpoint)
├── database.py            ← SQLite CRUD operatsiyalari
├── aqi_calculator.py      ← AQI hisoblash (EPA standartlari)
├── ml_predictor.py        ← ML placeholder (kelajakda LSTM)
├── telegram_alert.py      ← Telegram ogohlantirish (ixtiyoriy)
├── templates/
│   ├── index.html         ← Asosiy dashboard
│   ├── history.html       ← Tarix va grafiklar
│   └── about.html         ← Loyiha haqida
├── static/
│   ├── style.css          ← Umumiy dizayn
│   └── script.js          ← Umumiy JavaScript utilitalar
├── arduino/
│   └── esp32_full.ino     ← ESP32 to'liq kodi
├── logs/
│   └── server.log         ← Server loglari (avtomatik)
├── requirements.txt       ← Python paketlari
├── .env.example           ← Sozlamalar namunasi
├── start.bat              ← Windows bir bosishda ishga tushirish
└── havo_data.db           ← SQLite baza (avtomatik yaratiladi)
```

---

## 1-qadam: Python o'rnatish

Python **3.10** yoki yangi versiya kerak.

1. [python.org](https://python.org/downloads) dan yuklab o'rnating
2. O'rnatishda **"Add Python to PATH"** katagini belgilang
3. Tekshirish: `cmd` oching → `python --version`

---

## 2-qadam: Serverni ishga tushirish

### Usul A — Avtomatik (tavsiya etiladi)

`start.bat` faylini **ikki marta bosing**. U:
- Barcha paketlarni o'rnatadi
- Kompyuter IP manzilini ko'rsatadi
- Brauzerda dashboard ni ochadi
- Serverni ishga tushiradi

### Usul B — Terminal orqali

```cmd
cd C:\Users\seed\Documents\diplom_server

pip install -r requirements.txt

python server.py
```

Muvaffaqiyatli ishga tushganda:
```
INFO | server | Server ishga tushdi!
INFO | server | Dashboard -> http://localhost:8000
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 3-qadam: Kompyuter IP manzilini topish

```cmd
ipconfig
```
`Wireless LAN adapter Wi-Fi` → `IPv4 Address` qatorini toping.
Masalan: `192.168.1.105`

> `start.bat` ishga tushganda IP manzilni avtomatik ko'rsatadi.

---

## 4-qadam: ESP32 ni sozlash

`arduino/esp32_full.ino` faylini **Arduino IDE** da oching.

Faqat shu 2 ta qatorni o'zgartiring (12–15 qatorlar):

```cpp
const char* WIFI_SSID  = "SIZNING_WIFI_NOMI";        // ← o'zgartiring
const char* WIFI_PAROL = "SIZNING_WIFI_PAROLI";      // ← o'zgartiring
const char* SERVER_URL = "http://192.168.1.105:8000/api/sensor"; // ← o'zgartiring
```

### Arduino IDE sozlamalari

**Kutubxona o'rnatish** (Tools → Manage Libraries):
- `ArduinoJson` (Benoit Blanchon)

**Board o'rnatish** (File → Preferences → Additional Boards Manager URLs):
```
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
```
Tools → Board → Boards Manager → `esp32` qidiring → o'rnating.

**Board tanlash:** Tools → Board → `ESP32 Dev Module`

### Yuklab olish va tekshirish

1. `Upload` tugmasini bosing
2. `Serial Monitor` oching (baud: **115200**)
3. Quyidagi xabar ko'rinishi kerak:
```
Wi-Fi ga ulandi!
   IP manzili: 192.168.1.210
Qurilma tayyor!
```

---

## 5-qadam: Web saytga kirish

| Qurilma | Manzil |
|---------|--------|
| Kompyuterdan | http://localhost:8000 |
| Telefon/planshetdan | http://[KOMPYUTER_IP]:8000 |

### Sahifalar

- `/` — Asosiy dashboard (AQI, sensorlar, grafik)
- `/history` — Tarix va statistika
- `/about` — Loyiha haqida

---

## API endpointlar

| Method | URL | Tavsif |
|--------|-----|--------|
| POST | `/api/sensor` | ESP32 ma'lumot yuboradi |
| GET | `/api/aqi` | Hozirgi AQI va daraja |
| GET | `/api/data?soat=1&limit=50` | Sensor ma'lumotlari |
| GET | `/api/predict` | Keyingi 1 soat bashorati |
| GET | `/api/stats?soat=24` | Statistika |
| GET | `/api/export/csv` | CSV yuklab olish (ML uchun) |

### Test (ESP32 simulyatsiyasi)

```cmd
curl -X POST http://localhost:8000/api/sensor ^
  -H "Content-Type: application/json" ^
  -d "{\"device_id\":\"test\",\"mq135\":1,\"mq2\":0}"
```

---

## Telegram ogohlantirish (ixtiyoriy)

1. `.env.example` faylini `.env` nomi bilan nusxalang
2. `.env` faylini tahrirlang:
   ```
   TELEGRAM_BOT_TOKEN=1234567890:ABCdef...
   TELEGRAM_CHAT_ID=987654321
   AQI_CHEGARA=150
   ```
3. Bot yaratish: [@BotFather](https://t.me/BotFather) → `/newbot`
4. Chat ID: [@userinfobot](https://t.me/userinfobot) ga yozing

---

## Ko'p uchraydigan muammolar

### ❌ `ModuleNotFoundError`
```cmd
pip install -r requirements.txt
```

### ❌ ESP32 serverga ulana olmayapti
1. Kompyuter va ESP32 **bir xil Wi-Fi** ga ulangan bo'lsin
2. `SERVER_URL` dagi IP manzilni tekshiring
3. Windows Firewall:
   ```cmd
   netsh advfirewall firewall add rule name="HavoSifati" dir=in action=allow protocol=TCP localport=8000
   ```

### ❌ `Address already in use` — 8000-port band
```cmd
netstat -ano | findstr :8000
taskkill /PID [PID_RAQAMI] /F
```

### ❌ MQ sensor doim "Gaz aniqlandi" ko'rsatmoqda
- Sensor **2–3 daqiqa isitish** vaqti kerak
- Potentiometr (DO pin yonidagi) bilan sezgirlikni rostlang

### ❌ Dashboard yangilanmayapti
- `F12` → Console — xatoni ko'ring
- Server terminal da xato bormi — tekshiring

---

## Yangi sensor qo'shish (kelajak uchun)

1. `arduino/esp32_full.ino` da:
   - `ENABLE_[SENSOR] = true` qiling
   - Sensor o'qish kodini yoching

2. `server.py` → `SensorMalumot` modeliga yangi maydon qo'shing

3. `database.py` → `measurements` jadvaliga ustun qo'shing (migration)

4. `aqi_calculator.py` → `get_overall_aqi` funksiyasini yangilang

---

## LSTM modeli (kelajakdagi bosqich)

CSV ma'lumotlar yig'ilgach (`/api/export/csv`):

```python
# ml_training.ipynb (Jupyter Notebook)
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

df = pd.read_csv('havo_data.csv')
# ... model yaratish va o'qitish
```

`ml_predictor.py` dagi `predict_next_hour` funksiyasini LSTM model bilan almashtiring.

---

## Diplom himoyasi uchun maslahatlar

1. **Demo uchun** test ma'lumot yuboring:
   ```cmd
   curl -X POST http://localhost:8000/api/sensor -H "Content-Type: application/json" -d "{\"device_id\":\"demo\",\"mq135\":1,\"mq2\":1}"
   ```

2. **CSV eksport** ko'rsating: `/api/export/csv`

3. **Tarix sahifasi** da 7 kun / 30 kun oralig'ini ko'rsating

4. **AQI darajalari** haqida EPA standartlariga havola qiling

---

*Diplom ishi | 2025*
=======
# havo-sifati-monitoringi
Diplom ishi - ESP32 asosida havo sifati monitoringi
>>>>>>> 362e2c1ba9391f282d37e1ec52f3a4e9f8fea93c
