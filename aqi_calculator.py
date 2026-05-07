"""
AQI (Air Quality Index) hisoblash moduli
EPA (US Environmental Protection Agency) standartlari asosida.
"""

# ─── EPA breakpointlar: (c_past, c_yuqori, i_past, i_yuqori) ───

PM25_BREAKPOINTS = [
    (0.0,   12.0,  0,   50),
    (12.1,  35.4,  51,  100),
    (35.5,  55.4,  101, 150),
    (55.5,  150.4, 151, 200),
    (150.5, 250.4, 201, 300),
    (250.5, 350.4, 301, 400),
    (350.5, 500.4, 401, 500),
]

PM10_BREAKPOINTS = [
    (0,   54,  0,   50),
    (55,  154, 51,  100),
    (155, 254, 101, 150),
    (255, 354, 151, 200),
    (355, 424, 201, 300),
    (425, 504, 301, 400),
    (505, 604, 401, 500),
]

CO_BREAKPOINTS = [
    (0.0,  4.4,  0,   50),
    (4.5,  9.4,  51,  100),
    (9.5,  12.4, 101, 150),
    (12.5, 15.4, 151, 200),
    (15.5, 30.4, 201, 300),
    (30.5, 40.4, 301, 400),
    (40.5, 50.4, 401, 500),
]

# ─── AQI darajalari ───
AQI_DARAJALARI = [
    (0,   50,  "Yaxshi",                     "#10b981"),
    (51,  100, "O'rtacha",                   "#f59e0b"),
    (101, 150, "Sezgir guruh uchun zararli", "#f97316"),
    (151, 200, "Zararli",                    "#ef4444"),
    (201, 300, "Juda zararli",               "#8b5cf6"),
    (301, 999, "Xavfli",                     "#78350f"),
]

# ─── Sog'liq maslahatlari ───
SOGLIQ_MASLAHAT = [
    (0,   50,  "Havo sifati a'lo! Tashqarida faol bo'ling, sport bilan shug'ullaning. 🌿"),
    (51,  100, "Havo sifati qoniqarli. Juda sezgir odamlar uzoq muddatli tashqi faoliyatni cheklashi mumkin. 😊"),
    (101, 150, "Sezgir guruhlar (bolalar, keksa odamlar, yurak/o'pka kasalliklari bor odamlar) tashqi faoliyatni cheklashi kerak. ⚠️"),
    (151, 200, "Barcha odamlar uzoq muddatli tashqi faoliyatni kamaytirishini tavsiya etamiz. Sezgir guruhlar ichkarida qolsin! 🚨"),
    (201, 300, "Sog'liq uchun favqulodda holat! Hamma tashqarida bo'lishini cheklashi kerak. 🆘"),
    (301, 999, "Sog'liq uchun jiddiy xavf! Tashqarida bo'lmang. Niqob kiyish majburiy! ☠️"),
]


def _hisoblash(c: float, breakpoints: list) -> int | None:
    """EPA AQI formulasi: chiziqli interpolatsiya."""
    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= c <= c_high:
            return round((i_high - i_low) / (c_high - c_low) * (c - c_low) + i_low)
    return 500 if c > breakpoints[-1][1] else None


def pm25_to_aqi(pm25: float) -> int | None:
    """PM2.5 (μg/m³) qiymatidan AQI hisoblash."""
    return _hisoblash(pm25, PM25_BREAKPOINTS)


def pm10_to_aqi(pm10: float) -> int | None:
    """PM10 (μg/m³) qiymatidan AQI hisoblash."""
    return _hisoblash(pm10, PM10_BREAKPOINTS)


def co_to_aqi(co_ppm: float) -> int | None:
    """CO (ppm) qiymatidan AQI hisoblash."""
    return _hisoblash(co_ppm, CO_BREAKPOINTS)


def binary_mq_aqi(sensor_id: str, value: int) -> int | None:
    """
    Raqamli (DO) MQ sensorlari uchun AQI taxmini.
    1 = toza (AQI ta'sir etmaydi), 0 = gaz aniqlandi.
    """
    if value == 1:
        return None
    return {"mq135": 151, "mq2": 201, "mq7": 151}.get(sensor_id, 151)


def get_overall_aqi(m: dict) -> int:
    """
    Barcha mavjud sensorlar qiymatlaridan eng yuqori AQI ni hisoblash.
    m — measurements yozuvi (dict).
    Agar hech qanday gaz aniqlanmasa 30 (Yaxshi) qaytariladi.
    """
    aqilar = []

    if m.get("pm25") is not None:
        v = pm25_to_aqi(m["pm25"])
        if v:
            aqilar.append(v)

    if m.get("pm10") is not None:
        v = pm10_to_aqi(m["pm10"])
        if v:
            aqilar.append(v)

    for sensor in ("mq135", "mq2", "mq7"):
        if m.get(sensor) is not None:
            v = binary_mq_aqi(sensor, m[sensor])
            if v:
                aqilar.append(v)

    return max(aqilar) if aqilar else 30


def get_aqi_category(aqi: int) -> dict:
    """AQI qiymati uchun daraja nomi va rangi."""
    for lo, hi, nomi, rang in AQI_DARAJALARI:
        if lo <= aqi <= hi:
            return {"aqi": aqi, "daraja": nomi, "rang": rang}
    return {"aqi": aqi, "daraja": "Noma'lum", "rang": "#64748b"}


def get_health_advice(aqi: int) -> str:
    """AQI asosida o'zbek tilidagi sog'liq maslahat."""
    for lo, hi, maslax in SOGLIQ_MASLAHAT:
        if lo <= aqi <= hi:
            return maslax
    return "Havo sifati o'ta xavfli! Zudlik bilan xavfsiz joyga o'ting. ☠️"
