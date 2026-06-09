═══════════════════════════════════════════════════════════════
AQI DARAJALARI VA TAVSIYALAR — TO'LIQ RO'YXAT
Manba: aqi_calculator.py · server.py · templates/index.html
       ml_predictor.py · telegram_alert.py
═══════════════════════════════════════════════════════════════

══════════════════════════════════════════
ASOSIY AQI DARAJALARI VA TAVSIYALAR
══════════════════════════════════════════

1. YAXSHI (AQI 0–50)
   Rangi : #00E400 (yashil)
   Emoji : 🟢
   Daraja: "Yaxshi"

   Dashboard AQI jadvali:
   - Sog'liq ta'siri : "Havo toza — hech qanday xavf yo'q"
   - Tavsiya          : "Tashqarida erkin sayr qilsa bo'ladi"

   Hozirgi holat kartasi (tavsiyalar_royxat):
   - Sarlavha: "AQI [son] — Yaxshi"
   - Matn    : "Havo toza. Tashqarida erkin sayr qilish mumkin."

   Tarix/grafik tooltip:
   - "Yaxshi"

──────────────────────────────────────────

2. O'RTACHA (AQI 51–100)
   Rangi : #FFFF00 / #f59e0b (sariq)
   Emoji : 🟡
   Daraja: "O'rtacha"

   Dashboard AQI jadvali:
   - Sog'liq ta'siri : "Sezgir odamlar uchun yengil ta'sir mumkin"
   - Tavsiya          : "Nafas kasalligi bo'lganlar uzoq muddatli tashqaridagi faoliyatni cheklash kerak"

   Hozirgi holat kartasi (tavsiyalar_royxat):
   - Sarlavha: "AQI [son] — O'rtacha"
   - Matn    : "Havo qoniqarli. Sezgir odamlar uzoq muddatli mashqlarni cheklashi tavsiya etiladi."

   Tarix/grafik tooltip:
   - "O'rtacha"

──────────────────────────────────────────

3. SEZGIRLARGA ZARARLI (AQI 101–150)
   Rangi : #FF7E00 / #f97316 (to'q sariq)
   Emoji : 🟠
   Daraja: "Sezgir guruh uchun zararli"

   Dashboard AQI jadvali:
   - Sog'liq ta'siri : "Bolalar, keksalar, astma va yurak kasallar uchun havf"
   - Tavsiya          : "Sezgir guruh tashqi faoliyatni cheklasin; qolganlar ehtiyot bo'lsin"

   Hozirgi holat kartasi (tavsiyalar_royxat):
   - Sarlavha: "AQI [son] — Sezgir guruh uchun zararli"
   - Matn    : "Bolalar, keksalar va yurak/nafas kasalligi bor kishilar tashqari faoliyatini cheklasin."

   Tarix/grafik tooltip:
   - "Sezgir guruh uchun"

──────────────────────────────────────────

4. ZARARLI (AQI 151–200)
   Rangi : #FF0000 / #ef4444 (qizil)
   Emoji : 🔴
   Daraja: "Zararli"

   Dashboard AQI jadvali:
   - Sog'liq ta'siri : "Barcha aholi sog'liqqa salbiy ta'sir sezishi mumkin"
   - Tavsiya          : "Hamma tashqi faoliyatni kamaytirsin; sezgirlar ichkarida qolsin"

   Hozirgi holat kartasi (tavsiyalar_royxat):
   - Sarlavha: "AQI [son] — Zararli"
   - Matn    : "Barcha kishilar tashqari faoliyatni kamaytirishini tavsiya etamiz. Sezgir guruhlar ichkarida qolsin!"

   Tarix/grafik tooltip:
   - "Zararli"

──────────────────────────────────────────

5. JUDA ZARARLI (AQI 201–300)
   Rangi : #8F3F97 / #8b5cf6 (binafsha)
   Emoji : 🟣
   Daraja: "Juda zararli"

   Dashboard AQI jadvali:
   - Sog'liq ta'siri : "Jiddiy sog'liq xavfi"
   - Tavsiya          : "Tashqarida chiqmang; niqob majburiy; derazani yoping"

   Hozirgi holat kartasi (tavsiyalar_royxat):
   - Sarlavha: "AQI [son] — Juda zararli"
   - Matn    : "Sog'liq uchun favqulodda holat! Niqob kiyish tavsiya etiladi."

   Tarix/grafik tooltip:
   - "Juda zararli"

──────────────────────────────────────────

6. XAVFLI (AQI 301–500)
   Rangi : #7E0023 (to'q qizil)
   Emoji : ⚫
   Daraja: "Xavfli"

   Dashboard AQI jadvali:
   - Sog'liq ta'siri : "Favqulodda holat — butun aholi uchun xavfli"
   - Tavsiya          : "Mutlaqo tashqarida bo'lmang; zudlik bilan tibbiy yordam oling"

   Hozirgi holat kartasi (tavsiyalar_royxat):
   - Sarlavha: "AQI [son] — Xavfli"
   - Matn    : "Jiddiy sog'liq xavfi! Tashqarida mutlaqo bo'lmang. Zudlik bilan tibbiy yordam oling."

   Tarix/grafik tooltip:
   - "Juda zararli"  (AQI > 200 uchun grafik label)


══════════════════════════════════════════
QO'SHIMCHA TAVSIYALAR (SHAROITGA QARAB)
══════════════════════════════════════════

── PM2.5 chang zarrachalari (PMS5003 sensori) ──────────────

  PM2.5 > 150.4 μg/m³ (Juda yuqori):
  - Sarlavha : "PM2.5 juda yuqori"
  - Matn     : "PM2.5 = [qiymat] μg/m³ — niqob kiyish majburiy, tashqarida bo'lmang"
  - Rang     : #ef4444 (qizil)  |  Ikon: 🔴

  PM2.5 55.5–150.4 μg/m³ (Yuqori):
  - Sarlavha : "PM2.5 yuqori"
  - Matn     : "PM2.5 = [qiymat] μg/m³ — sezgir guruh tashqarida bo'lmasin"
  - Rang     : #f97316 (to'q sariq)  |  Ikon: 🟠

  PM2.5 35.5–55.4 μg/m³ (Ko'tarilgan):
  - Sarlavha : "PM2.5 ko'tarilgan"
  - Matn     : "PM2.5 = [qiymat] μg/m³ — uzoq muddatli mashqni cheklang"
  - Rang     : #f59e0b (sariq)  |  Ikon: 🟡

── PM10 chang zarrachalari ─────────────────────────────────

  PM10 > 154 μg/m³:
  - Sarlavha : "PM10 yuqori"
  - Matn     : "PM10 = [qiymat] μg/m³ — chang zarrachalari miqdori oshgan"
  - Rang     : #f97316 (to'q sariq)  |  Ikon: 🟠

── Harorat ─────────────────────────────────────────────────

  Harorat > 38°C (Juda issiq):
  - Sarlavha : "Juda issiq"
  - Matn     : "Harorat [qiymat]°C — ko'p suv iching, soyada dam oling"
  - Rang     : #ef4444 (qizil)  |  Ikon: 🌡️

  Harorat 35–38°C (Issiq):
  - Sarlavha : "Issiq"
  - Matn     : "Harorat [qiymat]°C — suyuqlik ko'proq iching"
  - Rang     : #f97316 (to'q sariq)  |  Ikon: 🌡️

  Harorat < 5°C (Sovuq):
  - Sarlavha : "Sovuq havo"
  - Matn     : "Harorat [qiymat]°C — iliq kiyining, nafas yo'llarini himoya qiling"
  - Rang     : #60a5fa (ko'k)  |  Ikon: ❄️

── Namlik ──────────────────────────────────────────────────

  Namlik > 85% (Juda yuqori):
  - Sarlavha : "Namlik juda yuqori"
  - Matn     : "Namlik [qiymat]% — o'pkaga og'irlik tushadi, faoliyatni cheklang"
  - Rang     : #f97316 (to'q sariq)  |  Ikon: 💧

  Namlik < 20% (Juda quruq):
  - Sarlavha : "Havo quruq"
  - Matn     : "Namlik [qiymat]% — shilliq pardani himoya qilish uchun ko'proq suv iching"
  - Rang     : #f59e0b (sariq)  |  Ikon: 🏜️

── Atmosfera bosimi ─────────────────────────────────────────

  Bosim < 990 hPa (Past):
  - Sarlavha : "Bosim past"
  - Matn     : "Atmosfera bosimi [qiymat] hPa — bosh og'riq bo'lishi mumkin"
  - Rang     : #8b5cf6 (binafsha)  |  Ikon: ⬇️

  Bosim > 1030 hPa (Yuqori):
  - Sarlavha : "Bosim yuqori"
  - Matn     : "Atmosfera bosimi [qiymat] hPa — havo barqaror"
  - Rang     : #10b981 (yashil)  |  Ikon: ⬆️

── MQ gaz sensorlari (DO = 0 — gaz aniqlandi) ──────────────

  MQ-135 (CO₂, NH₃, Benzol):
  - Sarlavha : "Gaz aniqlandi"
  - Matn     : "CO₂ va NH₃ darajasi yuqori (MQ-135 sensori signal berdi)"
  - Rang     : #ef4444 (qizil)  |  Ikon: ⚠️

  MQ-2 (Metan, LPG, Tutun):
  - Sarlavha : "Gaz aniqlandi"
  - Matn     : "Tutun, metan yoki LPG aniqlandi (MQ-2 sensori signal berdi)"
  - Rang     : #ef4444 (qizil)  |  Ikon: ⚠️

  MQ-7 (CO — Uglerod oksidi):
  - Sarlavha : "Gaz aniqlandi"
  - Matn     : "Uglerod oksidi (CO) aniqlandi — xavfli! (MQ-7 sensori signal berdi)"
  - Rang     : #ef4444 (qizil)  |  Ikon: ⚠️

── AQI aralash tavsiya (sog_liq_tavsiya — server javob) ────

  Asosiy matn + qo'shimcha sharoit:
  - "[AQI daraja tavsiyasi] | Harorat juda yuqori ([qiymat]°C) — ko'p suv iching, soyada dam oling."
  - "[AQI daraja tavsiyasi] | Harorat yuqori ([qiymat]°C) — suyuqlik ko'proq iching."
  - "[AQI daraja tavsiyasi] | Havo sovuq ([qiymat]°C) — iliq kiyining, nafas yo'llarini himoya qiling."
  - "[AQI daraja tavsiyasi] | Namlik juda yuqori ([qiymat]%) — o'pkaga og'irlik tushadi, faoliyatni cheklang."
  - "[AQI daraja tavsiyasi] | Havo juda quruq ([qiymat]%) — shilliq pardani himoya qilish uchun ko'proq suv iching."


══════════════════════════════════════════
SENSOR HOLATI XABARLARI
══════════════════════════════════════════

── MQ sensorlar uchun sensor_holati() ─────────────────────

  Barcha sensorlar toza:
  - "Barcha sensorlar normal — havo toza"

  MQ-135 gaz aniqladi:
  - "CO₂ va NH₃ darajasi yuqori (MQ-135 sensori signal berdi)"

  MQ-2 gaz aniqladi:
  - "Tutun, metan yoki LPG aniqlandi (MQ-2 sensori signal berdi)"

  MQ-7 gaz aniqladi:
  - "Uglerod oksidi (CO) aniqlandi — xavfli! (MQ-7 sensori signal berdi)"

── Anomaliya aniqlash (ml_predictor.detect_anomaly) ────────

  AQI keskin o'zgarsa:
  - "AQI ([hozir]) tarixiy o'rtamadan ([orta]) keskin farqli."

  MQ-2 yonuvchan gaz:
  - "Yonuvchan gaz aniqlandi (MQ-2)."

  MQ-135 zararli gaz:
  - "Zararli gaz aniqlandi (MQ-135)."

  MQ-7 CO gaz:
  - "CO aniqlandi (MQ-7)."


══════════════════════════════════════════
LSTM BASHORAT XABARLARI
══════════════════════════════════════════

── Statistik bashorat (ml_predictor.py) ────────────────────

  Ma'lumot yetarli:
  - "So'nggi [N] ta o'lchovga asoslangan statistik bashorat. LSTM aniqroq natija uchun: python ml/train_model.py"

  Ma'lumot kam (1 ta):
  - "Faqat [N] ta AQI qiymati. Kamida 2 ta kerak."

  Ma'lumot yo'q:
  - "Bashorat uchun yetarli ma'lumot yo'q. Sensor ma'lumotlari kutilmoqda."

── Trend ko'rsatkichlari (index.html bashoratYanila) ────────

  AQI + 10 dan oshsa:
  - "📈 Yomonlashadi"  (qizil rang)

  AQI - 10 dan tushsa:
  - "📉 Yaxshilanadi"  (yashil rang)

  ±10 oraliqda:
  - "➡️ Barqaror"  (kulrang)

  Qurilma offline:
  - "⊘ Bashorat mumkin emas"
  - "Qurilma offline — bashorat mumkin emas."

  Bashorat yuklanmadi:
  - "Bashorat yuklanmadi. Qayta urinilmoqda..."

  Ma'lumot yig'ilmoqda:
  - "Ma'lumot yig'ilmoqda"
  - "Bashorat uchun yetarli ma'lumot yo'q."


══════════════════════════════════════════
OFFLINE / ULANISH XABARLARI
══════════════════════════════════════════

  Qurilma offline banneri:
  - "⚠️ Qurilma bilan aloqa yo'q!"
  - "Oxirgi ko'rinish: [vaqt]"

  AQI/tavsiya kartasi (offline):
  - "⚠️ Qurilma bilan aloqa yo'q!"
  - API javobi: "Qurilma bilan aloqa yo'q! So'nggi ma'lumot yangilanmayapti."

  Sensor kartasi (offline):
  - "Aloqa yo'q"
  - "Qurilma offline"

  Server xato banner:
  - "⚠️ Server bilan bog'liq muammo. Qayta ulanilmoqda..."

  AQI qiymati mavjud bo'lmasa:
  - "Noma'lum"


══════════════════════════════════════════
TELEGRAM OGOHLANTIRISH XABARI (AQI ≥ 150)
══════════════════════════════════════════

  Har 30 daqiqada bir marta yuboriladi:

  🚨 HAVO SIFATI OGOHLANTIRISHII

  📅 Vaqt: [dd.mm.yyyy hh:mm] (Toshkent)
  📊 AQI: [son] — [daraja]

  📡 Sensor holatlari:
    • MQ-135 (CO₂/NH₃): ✅ Toza | 🚨 Gaz!
    • MQ-2 (Metan/LPG): ✅ Toza | 🚨 Gaz!
    • MQ-7 (CO): ✅ Toza | 🚨 Gaz!
    • PM2.5 (μg/m³): [qiymat]
    • PM10 (μg/m³): [qiymat]
    • Harorat (°C): [qiymat]

  ⚠️ Tashqarida bo'lishingizni cheklang.
  🌐 Dashboard: http://localhost:8000


══════════════════════════════════════════
SIDEBAR SENSOR HOLATLARI
══════════════════════════════════════════

  MQ sensorlar (DO signal):
  - DO = 1 (toza) → "✓"  (yashil)
  - DO = 0 (gaz)  → "!"  (qizil)
  - Ulanmagan     → "—"  (kulrang)

  MQ Gaz jadvali (DO izoh):
  - "DO = 1 → gaz chegaradan past (TOZA)"
  - "DO = 0 → gaz aniqlandi (GAZ!)"

  Qurilma holati:
  - Online  → "Online"  (yashil nuqta)
  - Offline → "Offline" (qizil nuqta)

  Status bar:
  - "● Online"  (yashil)
  - "● Offline" (qizil)
  - "● Kutilmoqda" (kulrang)


═══════════════════════════════════════════════════════════════
AQI CHEGARA QIYMATLARI (HISOBLASH UCHUN)
═══════════════════════════════════════════════════════════════

  MQ DO sensor kombinatsiyasi → AQI:
  - 0 ta iflos sensor → AQI 30  (Yaxshi)
  - 1 ta iflos sensor → AQI 75  (O'rtacha)
  - 2 ta iflos sensor → AQI 125 (Sezgir guruh)
  - 3 ta iflos sensor → AQI 175 (Zararli)
  + Harorat > 35°C   → AQI + 25
  + Namlik  > 80%    → AQI + 15

  Bosim ta'siri AQI ga:
  - Bosim < 990 hPa  → AQI + 10
  - Bosim > 1030 hPa → AQI − 5

  PM2.5 EPA o'tish nuqtalari (μg/m³ → AQI):
  -   0.0–12.0   →   0–50
  -  12.1–35.4   →  51–100
  -  35.5–55.4   → 101–150
  -  55.5–150.4  → 151–200
  - 150.5–250.4  → 201–300
  - 250.5–350.4  → 301–400
  - 350.5–500.4  → 401–500

═══════════════════════════════════════════════════════════════
Saqlandi: docs/tavsiyalar_royxati.md  |  2026-06-07
═══════════════════════════════════════════════════════════════
