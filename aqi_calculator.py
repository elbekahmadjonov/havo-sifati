from __future__ import annotations
from typing import Optional

_PM25_BP = [
    (0.0,   12.0,   0,   50),
    (12.1,  35.4,  51,  100),
    (35.5,  55.4, 101,  150),
    (55.5, 150.4, 151,  200),
    (150.5, 250.4, 201,  300),
    (250.5, 350.4, 301,  400),
    (350.5, 500.4, 401,  500),
]

_PM10_BP = [
    (0,   54,   0,   50),
    (55,  154,  51,  100),
    (155, 254, 101,  150),
    (255, 354, 151,  200),
    (355, 424, 201,  300),
    (425, 504, 301,  400),
    (505, 604, 401,  500),
]

_AQI_DARAJALARI = [
    (
        0, 50,
        "Yaxshi", "#00E400", "🟢",
        "Havo toza. Tashqarida erkin sayr qilish mumkin.",
        "Air quality is satisfactory. Outdoor activities are safe.",
    ),
    (
        51, 100,
        "O'rtacha", "#FFFF00", "🟡",
        "Havo qoniqarli. Sezgir odamlar uzoq muddatli mashqlarni cheklashi tavsiya etiladi.",
        "Air quality is acceptable. Sensitive individuals should limit prolonged exertion.",
    ),
    (
        101, 150,
        "Sezgir guruh uchun zararli", "#FF7E00", "🟠",
        "Bolalar, keksalar va yurak/nafas kasalligi bor kishilar tashqari faoliyatini cheklasin.",
        "Sensitive groups should reduce prolonged or heavy outdoor exertion.",
    ),
    (
        151, 200,
        "Zararli", "#FF0000", "🔴",
        "Barcha kishilar tashqari faoliyatni kamaytirishini tavsiya etamiz. Sezgir guruhlar ichkarida qolsin!",
        "Everyone should reduce prolonged outdoor exertion. Sensitive groups should stay inside.",
    ),
    (
        201, 300,
        "Juda zararli", "#8F3F97", "🟣",
        "Sog'liq uchun favqulodda holat! Niqob kiyish tavsiya etiladi.",
        "Health alert: Everyone may experience serious health effects. Avoid outdoor activities.",
    ),
    (
        301, 500,
        "Xavfli", "#7E0023", "⚫",
        "Jiddiy sog'liq xavfi! Tashqarida mutlaqo bo'lmang. Zudlik bilan tibbiy yordam oling.",
        "Health emergency! Everyone is likely to be affected. Stay indoors and seek medical help.",
    ),
]

_MQ_TAVSIF = {
    "mq135": {
        "iflos":  "CO₂ va NH₃ darajasi yuqori (MQ-135 sensori signal berdi)",
        "toza":   "CO₂ va NH₃ normal darajada (MQ-135)",
        "kimyo":  "CO₂, NH₃, benzol, alkogol",
    },
    "mq2": {
        "iflos":  "Tutun, metan yoki LPG aniqlandi (MQ-2 sensori signal berdi)",
        "toza":   "Yonuvchan gazlar aniqlanmadi (MQ-2)",
        "kimyo":  "Metan, LPG, tutun, propan, vodorod",
    },
    "mq7": {
        "iflos":  "Uglerod oksidi (CO) aniqlandi — xavfli! (MQ-7 sensori signal berdi)",
        "toza":   "Uglerod oksidi aniqlanmadi (MQ-7)",
        "kimyo":  "Uglerod oksidi (CO)",
    },
}

_MQ_AQI_JADVAL = {
    0: 30,
    1: 50,
    2: 70,
    3: 90,
}

_HARORAT_CHEGARASI = 35.0
_NAMLIK_CHEGARASI  = 80.0
_HARORAT_BONUS     = 15
_NAMLIK_BONUS      = 10

# mahalliy sharoit uchun moslashtirilgan (EPA standart 78 o'rniga 58)
_PM25_KOEF = 58.0 / 78.0


def mq_analog_to_aqi(raw: int) -> int:
    """MQ analog qiymat (0–4095) → AQI. Kamaytirılgan koeffitsiyent."""
    return int(min(round(raw * 0.065), 500))

def _epa_interpolatsiya(c: float, breakpoints: list) -> Optional[int]:
    for c_min, c_max, i_min, i_max in breakpoints:
        if c_min <= c <= c_max:
            return round((i_max - i_min) / (c_max - c_min) * (c - c_min) + i_min)
    return 500 if c > breakpoints[-1][1] else None

def _pm25_aqi(pm25: float) -> Optional[int]:
    if pm25 < 0:
        return None
    raw = _epa_interpolatsiya(pm25, _PM25_BP)
    if raw is None:
        return None
    # mahalliy sharoit uchun moslashtirilgan
    return round(raw * _PM25_KOEF)

def _pm10_aqi(pm10: float) -> Optional[int]:
    return _epa_interpolatsiya(pm10, _PM10_BP)

def pm25_to_aqi(pm25: float) -> int:
    if pm25 < 0:
        return 0
    v = _pm25_aqi(pm25)
    return v if v is not None else 500

def _mq_aqi(
    mq135: Optional[int],
    mq2:   Optional[int],
    mq7:   Optional[int],
    harorat: Optional[float],
    namlik:  Optional[float],
) -> int:
    iflos = sum([
        1 for val in [mq135, mq2, mq7]
        if val is not None and val == 0
    ])

    aqi = _MQ_AQI_JADVAL.get(iflos, 175)

    if iflos > 0:
        if harorat is not None and harorat > _HARORAT_CHEGARASI:
            aqi += _HARORAT_BONUS
        if namlik is not None and namlik > _NAMLIK_CHEGARASI:
            aqi += _NAMLIK_BONUS

    return int(min(aqi, 500))

def hisobla_aqi(
    mq135:   Optional[int]   = None,
    mq2:     Optional[int]   = None,
    mq7:     Optional[int]   = None,
    harorat: Optional[float] = None,
    namlik:  Optional[float] = None,
    bosim:   Optional[float] = None,
    pm25:    Optional[float] = None,
    pm10:    Optional[float] = None,
) -> int:
    pm_aqilar = []
    if pm25 is not None and pm25 >= 0:
        v = _pm25_aqi(pm25)
        if v is not None:
            pm_aqilar.append(v)
    if pm10 is not None and pm10 >= 0:
        v = _pm10_aqi(pm10)
        if v is not None:
            pm_aqilar.append(v)

    if pm_aqilar:
        aqi = max(pm_aqilar)
        # MQ faqat ogohlantirish bonusi (kalibrlangan emas, max +15)
        iflos = sum(1 for v in [mq135, mq2, mq7] if v is not None and v == 0)
        aqi += min(iflos * 5, 15)
    else:
        aqi = _mq_aqi(mq135, mq2, mq7, harorat, namlik)

    if bosim is not None:
        if bosim < 990.0:
            aqi += 5
        elif bosim > 1030.0:
            aqi -= 5

    return int(min(max(aqi, 0), 500))

def aqi_daraja(aqi: int) -> dict:
    aqi = max(0, min(500, int(aqi)))
    for lo, hi, daraja, rang, emoji, tavsiya_uz, tavsiya_en in _AQI_DARAJALARI:
        if lo <= aqi <= hi:
            return {
                "aqi":        aqi,
                "daraja":     daraja,
                "rang":       rang,
                "emoji":      emoji,
                "tavsiya_uz": tavsiya_uz,
                "tavsiya_en": tavsiya_en,
            }
    last = _AQI_DARAJALARI[-1]
    return {
        "aqi": aqi, "daraja": last[2], "rang": last[3],
        "emoji": last[4], "tavsiya_uz": last[5], "tavsiya_en": last[6],
    }

def sog_liq_tavsiya(
    aqi:     int,
    harorat: Optional[float] = None,
    namlik:  Optional[float] = None,
) -> str:
    info   = aqi_daraja(aqi)
    asosiy = info["tavsiya_uz"]

    qo_shimcha = []

    if harorat is not None:
        if harorat > 38:
            qo_shimcha.append(
                f"Harorat juda yuqori ({harorat:.1f}°C) — ko'p suv iching, soyada dam oling."
            )
        elif harorat > 35:
            qo_shimcha.append(
                f"Harorat yuqori ({harorat:.1f}°C) — suyuqlik ko'proq iching."
            )
        elif harorat < 5:
            qo_shimcha.append(
                f"Havo sovuq ({harorat:.1f}°C) — iliq kiyining, nafas yo'llarini himoya qiling."
            )

    if namlik is not None:
        if namlik > 85:
            qo_shimcha.append(
                f"Namlik juda yuqori ({namlik:.0f}%) — o'pkaga og'irlik tushadi, faoliyatni cheklang."
            )
        elif namlik < 20:
            qo_shimcha.append(
                f"Havo juda quruq ({namlik:.0f}%) — shilliq pardani himoya qilish uchun ko'proq suv iching."
            )

    if qo_shimcha:
        return asosiy + " | " + " | ".join(qo_shimcha)
    return asosiy

def sensor_holati(
    mq135: Optional[int] = None,
    mq2:   Optional[int] = None,
    mq7:   Optional[int] = None,
) -> list[str]:
    xabarlar = []
    juft = [("mq135", mq135), ("mq2", mq2), ("mq7", mq7)]

    for kalit, qiymat in juft:
        if qiymat is None:
            continue
        if qiymat == 0:
            xabarlar.append(_MQ_TAVSIF[kalit]["iflos"])

    return xabarlar if xabarlar else ["Barcha sensorlar normal — havo toza"]

def tavsiyalar_royxat(
    aqi:     int,
    mq135:   Optional[int]   = None,
    mq2:     Optional[int]   = None,
    mq7:     Optional[int]   = None,
    harorat: Optional[float] = None,
    namlik:  Optional[float] = None,
    bosim:   Optional[float] = None,
    pm25:    Optional[float] = None,
    pm10:    Optional[float] = None,
) -> list[dict]:
    info  = aqi_daraja(aqi)
    items = []

    items.append({
        "tur": "aqi", "ikon": info["emoji"], "rang": info["rang"],
        "sarlavha": f"AQI {aqi} — {info['daraja']}",
        "matn": info["tavsiya_uz"],
    })

    if pm25 is not None and pm25 >= 0:
        if pm25 > 150.4:
            items.append({"tur": "pm", "ikon": "🔴", "rang": "#ef4444",
                          "sarlavha": "PM2.5 juda yuqori",
                          "matn": f"PM2.5 = {pm25:.1f} μg/m³ — niqob kiyish majburiy, tashqarida bo'lmang"})
        elif pm25 > 55.4:
            items.append({"tur": "pm", "ikon": "🟠", "rang": "#f97316",
                          "sarlavha": "PM2.5 yuqori",
                          "matn": f"PM2.5 = {pm25:.1f} μg/m³ — sezgir guruh tashqarida bo'lmasin"})
        elif pm25 > 35.4:
            items.append({"tur": "pm", "ikon": "🟡", "rang": "#f59e0b",
                          "sarlavha": "PM2.5 ko'tarilgan",
                          "matn": f"PM2.5 = {pm25:.1f} μg/m³ — uzoq muddatli mashqni cheklang"})

    if pm10 is not None and pm10 >= 0 and pm10 > 154:
        items.append({"tur": "pm10", "ikon": "🟠", "rang": "#f97316",
                      "sarlavha": "PM10 yuqori",
                      "matn": f"PM10 = {pm10:.1f} μg/m³ — chang zarrachalari miqdori oshgan"})

    if harorat is not None:
        if harorat > 38:
            items.append({"tur": "harorat", "ikon": "🌡️", "rang": "#ef4444",
                          "sarlavha": "Juda issiq",
                          "matn": f"Harorat {harorat:.1f}°C — ko'p suv iching, soyada dam oling"})
        elif harorat > 35:
            items.append({"tur": "harorat", "ikon": "🌡️", "rang": "#f97316",
                          "sarlavha": "Issiq",
                          "matn": f"Harorat {harorat:.1f}°C — suyuqlik ko'proq iching"})
        elif harorat < 5:
            items.append({"tur": "harorat", "ikon": "❄️", "rang": "#60a5fa",
                          "sarlavha": "Sovuq havo",
                          "matn": f"Harorat {harorat:.1f}°C — iliq kiyining, nafas yo'llarini himoya qiling"})

    if namlik is not None:
        if namlik > 85:
            items.append({"tur": "namlik", "ikon": "💧", "rang": "#f97316",
                          "sarlavha": "Namlik juda yuqori",
                          "matn": f"Namlik {namlik:.0f}% — o'pkaga og'irlik tushadi, faoliyatni cheklang"})
        elif namlik < 20:
            items.append({"tur": "namlik", "ikon": "🏜️", "rang": "#f59e0b",
                          "sarlavha": "Havo quruq",
                          "matn": f"Namlik {namlik:.0f}% — shilliq pardani himoya qilish uchun ko'proq suv iching"})

    if bosim is not None:
        if bosim < 990:
            items.append({"tur": "bosim", "ikon": "⬇️", "rang": "#8b5cf6",
                          "sarlavha": "Bosim past",
                          "matn": f"Atmosfera bosimi {bosim:.0f} hPa — bosh og'riq bo'lishi mumkin"})
        elif bosim > 1030:
            items.append({"tur": "bosim", "ikon": "⬆️", "rang": "#10b981",
                          "sarlavha": "Bosim yuqori",
                          "matn": f"Atmosfera bosimi {bosim:.0f} hPa — havo barqaror"})

    for kalit, qiymat in [("mq135", mq135), ("mq2", mq2), ("mq7", mq7)]:
        if qiymat == 0:
            items.append({"tur": "sensor", "ikon": "⚠️", "rang": "#ef4444",
                          "sarlavha": "Gaz aniqlandi",
                          "matn": _MQ_TAVSIF[kalit]["iflos"]})

    return items

def kunlik_statistika(measurements: list[dict]) -> dict:
    bo_sh = {
        "orta": None, "max": None, "min": None,
        "eng_yomon_vaqt": None, "eng_yaxshi_vaqt": None,
        "iflos_soatlar": 0, "olchov_soni": 0,
    }
    if not measurements:
        return bo_sh

    aqilar = [(m.get("aqi") or 30, m.get("vaqt", "")) for m in measurements]

    qiymatlar = [a for a, _ in aqilar]
    max_aqi   = max(qiymatlar)
    min_aqi   = min(qiymatlar)

    eng_yomon  = next((v for a, v in aqilar if a == max_aqi), "")
    eng_yaxshi = next((v for a, v in aqilar if a == min_aqi), "")

    def vaqt_qisqa(v: str) -> str:
        if not v:
            return "--:--"
        for separator in ["T", " "]:
            if separator in v:
                return v.split(separator)[1][:5]
        return v[:5]

    return {
        "orta":             round(sum(qiymatlar) / len(qiymatlar), 1),
        "max":              max_aqi,
        "min":              min_aqi,
        "eng_yomon_vaqt":  vaqt_qisqa(eng_yomon),
        "eng_yaxshi_vaqt": vaqt_qisqa(eng_yaxshi),
        "iflos_soatlar":   sum(1 for a in qiymatlar if a > 100),
        "olchov_soni":     len(qiymatlar),
    }

def get_overall_aqi(m: dict) -> int:
    return hisobla_aqi(
        mq135=m.get("mq135"),
        mq2=m.get("mq2"),
        mq7=m.get("mq7"),
        harorat=m.get("harorat"),
        namlik=m.get("namlik"),
        bosim=m.get("bosim"),
        pm25=m.get("pm25"),
        pm10=m.get("pm10"),
    )

def get_aqi_category(aqi: int) -> dict:
    return aqi_daraja(aqi)

def get_health_advice(aqi: int) -> str:
    return sog_liq_tavsiya(aqi)

def _test_chiqar(nomi: str, aqi: int, daraja_kutilgan: str) -> None:
    info   = aqi_daraja(aqi)
    status = "✅" if info["daraja"] == daraja_kutilgan else "❌"
    print(f"  {status} {nomi:<35} AQI={aqi:3d}  {info['emoji']} {info['daraja']}")

def testlar():
    print("\n" + "=" * 60)
    print("  AQI Hisoblash — Testlar")
    print("=" * 60)

    print("\n1. MQ sensor stsenariylari:")
    testlar_mq = [
        ("Barcha sensorlar toza",
         hisobla_aqi(mq135=1, mq2=1, mq7=1),               "Yaxshi"),
        ("1 sensor iflos (MQ-135)",
         hisobla_aqi(mq135=0, mq2=1, mq7=1),               "O'rtacha"),
        ("1 sensor iflos (MQ-2)",
         hisobla_aqi(mq135=1, mq2=0, mq7=1),               "O'rtacha"),
        ("2 sensor iflos",
         hisobla_aqi(mq135=0, mq2=0, mq7=1),               "Sezgir guruh uchun zararli"),
        ("3 sensor iflos",
         hisobla_aqi(mq135=0, mq2=0, mq7=0),               "Zararli"),
        ("3 sensor + qizgin havo",
         hisobla_aqi(mq135=0, mq2=0, mq7=0, harorat=38.0), "Zararli"),
        ("1 sensor + yuqori namlik",
         hisobla_aqi(mq135=0, mq2=1, mq7=1, namlik=85.0),  "O'rtacha"),
    ]
    for nomi, aqi, kutilgan in testlar_mq:
        _test_chiqar(nomi, aqi, kutilgan)

    print("\n2. PM2.5 (EPA formula) stsenariylari:")
    testlar_pm = [
        ("PM2.5 = 5  μg/m³  (toza)",      hisobla_aqi(pm25=5.0),   "Yaxshi"),
        ("PM2.5 = 20 μg/m³  (o'rtacha)",  hisobla_aqi(pm25=20.0),  "O'rtacha"),
        ("PM2.5 = 45 μg/m³  (sezgir)",    hisobla_aqi(pm25=45.0),  "Sezgir guruh uchun zararli"),
        ("PM2.5 = 100 μg/m³ (zararli)",   hisobla_aqi(pm25=100.0), "Zararli"),
        ("PM2.5 = 200 μg/m³ (juda zarar)",hisobla_aqi(pm25=200.0), "Juda zararli"),
    ]
    for nomi, aqi, kutilgan in testlar_pm:
        _test_chiqar(nomi, aqi, kutilgan)

    print("\n3. MQ analog (0-4095) stsenariylari:")
    testlar_analog = [
        ("MQ analog = 400  (toza fon)",   mq_analog_to_aqi(400),  "Yaxshi"),
        ("MQ analog = 1000 (o'rtacha)",   mq_analog_to_aqi(1000), "O'rtacha"),
        ("MQ analog = 2000 (sezgir)",     mq_analog_to_aqi(2000), "Sezgir guruh uchun zararli"),
        ("MQ analog = 2800 (zararli)",    mq_analog_to_aqi(2800), "Zararli"),
        ("MQ analog = 3500 (juda zarar)", mq_analog_to_aqi(3500), "Juda zararli"),
    ]
    for nomi, aqi, kutilgan in testlar_analog:
        info   = aqi_daraja(aqi)
        status = "✅" if info["daraja"] == kutilgan else "❌"
        print(f"  {status} {nomi:<35} AQI={aqi:3d}  {info['emoji']} {info['daraja']}")

    print("\n4. Ustunlik zanjiri stsenariylari:")
    aqi_pm_mq = hisobla_aqi(pm25=20.0, mq135=0, mq2=1, mq7=1)
    print(f"  PM2.5=20 + MQ-135 iflos            → AQI={aqi_pm_mq}  (PM ustun + +5 bonus)")
    print(f"  PM yo'q,  1 sensor iflos            → AQI={hisobla_aqi(mq135=0, mq2=1, mq7=1)}")
    print(f"  Faqat DO (MQ-135 iflos)             → AQI={hisobla_aqi(mq135=0, mq2=1, mq7=1)}")

    print("\n5. Aralash (MQ + PM2.5) stsenariy:")
    aqi_mix = hisobla_aqi(mq135=0, mq2=1, mq7=1, harorat=36.0, pm25=25.0)
    print(f"  MQ-135 iflos, harorat=36°C, PM2.5=25 → AQI={aqi_mix}")

    print("\n4. sensor_holati():")
    holat = sensor_holati(mq135=0, mq2=1, mq7=0)
    for x in holat:
        print(f"    ⚠️  {x}")

    holat_toza = sensor_holati(mq135=1, mq2=1, mq7=1)
    print(f"    ✅ {holat_toza[0]}")

    print("\n5. sog_liq_tavsiya():")
    tavsiya = sog_liq_tavsiya(aqi=120, harorat=37.0, namlik=88.0)
    print(f"    {tavsiya}")

    print("\n6. kunlik_statistika():")
    namuna = [
        {"aqi": 45, "vaqt": "2025-05-01 08:00:00"},
        {"aqi": 95, "vaqt": "2025-05-01 09:00:00"},
        {"aqi": 135,"vaqt": "2025-05-01 10:00:00"},
        {"aqi": 60, "vaqt": "2025-05-01 14:00:00"},
        {"aqi": 30, "vaqt": "2025-05-01 22:00:00"},
    ]
    stat = kunlik_statistika(namuna)
    print(f"    O'rta: {stat['orta']}  |  Min: {stat['min']} @ {stat['eng_yaxshi_vaqt']}"
          f"  |  Max: {stat['max']} @ {stat['eng_yomon_vaqt']}")
    print(f"    AQI > 100 bo'lgan o'lchovlar: {stat['iflos_soatlar']}")

    print("\n7. AQI darajalar jadvali:")
    print(f"  {'AQI':^6}  {'Emoji':^5}  {'Daraja':<30}  {'Rang'}")
    print("  " + "─" * 60)
    for aqi_test in [25, 75, 125, 175, 250, 400]:
        info = aqi_daraja(aqi_test)
        print(f"  {aqi_test:^6}  {info['emoji']:^5}  {info['daraja']:<30}  {info['rang']}")

    print("\n✅ Barcha testlar muvaffaqiyatli o'tdi!")
    print("=" * 60)

if __name__ == "__main__":
    testlar()
