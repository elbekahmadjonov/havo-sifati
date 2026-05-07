"""
Telegram Ogohlantirish Moduli
AQI belgilangan chegaradan oshsa Telegram orqali xabar yuboradi.
.env faylida TELEGRAM_BOT_TOKEN va TELEGRAM_CHAT_ID sozlang.
"""
import os
import logging
import requests
from datetime import datetime, timedelta, timezone

log = logging.getLogger(__name__)

TOSHKENT_TZ     = timezone(timedelta(hours=5))
BOT_TOKEN       = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID         = os.getenv("TELEGRAM_CHAT_ID", "")
AQI_CHEGARA     = int(os.getenv("AQI_CHEGARA", "150"))
MIN_INTERVAL    = 30  # bir xil ogohlantirishni takrorlamaslik (daqiqa)

_oxirgi_yuborish: datetime | None = None


def telegram_faolmi() -> bool:
    """Telegram sozlamalari to'liq kiritilganmi?"""
    return bool(BOT_TOKEN and CHAT_ID)


def xabar_yuborish(matn: str) -> bool:
    """Telegram botiga xabar yuborish."""
    if not telegram_faolmi():
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, json={
            "chat_id":    CHAT_ID,
            "text":       matn,
            "parse_mode": "HTML",
        }, timeout=8)
        if r.ok:
            log.info("✅ Telegram xabari yuborildi.")
            return True
        log.warning("⚠️ Telegram API xatosi: %s", r.text)
    except requests.RequestException as e:
        log.error("❌ Telegram ulanish xatosi: %s", e)
    return False


def aqi_tekshir_va_xabarlash(aqi: int, daraja: str, sensor_holat: dict) -> bool:
    """
    AQI ni tekshirib, chegaradan oshsa Telegram xabari yuborish.
    MIN_INTERVAL daqiqada bir martadan ko'p xabar yubormaydi.
    """
    global _oxirgi_yuborish

    if aqi < AQI_CHEGARA:
        return False

    hozir = datetime.now(TOSHKENT_TZ)
    if _oxirgi_yuborish:
        delta_min = (hozir - _oxirgi_yuborish).total_seconds() / 60
        if delta_min < MIN_INTERVAL:
            return False

    # Sensor holati matnini shakllantirish
    qatorlar = []
    nom_map = {
        "mq135": "MQ-135 (CO₂/NH₃)", "mq2": "MQ-2 (Metan/LPG)",
        "mq7":   "MQ-7 (CO)",          "pm25": "PM2.5 (μg/m³)",
        "pm10":  "PM10 (μg/m³)",        "harorat": "Harorat (°C)",
    }
    for kalit, qiymat in sensor_holat.items():
        if qiymat is None:
            continue
        nom  = nom_map.get(kalit, kalit.upper())
        holat = ("✅ Toza" if qiymat == 1 else "🚨 Gaz!") if kalit in ("mq135", "mq2", "mq7") else str(qiymat)
        qatorlar.append(f"  • {nom}: {holat}")

    holat_matn = "\n".join(qatorlar) if qatorlar else "  Ma'lumot yo'q"
    vaqt_str   = hozir.strftime("%d.%m.%Y %H:%M")

    xabar = (
        f"🚨 <b>HAVO SIFATI OGOHLANTIRISHII</b>\n\n"
        f"📅 Vaqt: {vaqt_str} (Toshkent)\n"
        f"📊 AQI: <b>{aqi}</b> — {daraja}\n\n"
        f"📡 Sensor holatlari:\n{holat_matn}\n\n"
        f"⚠️ Tashqarida bo'lishingizni cheklang.\n"
        f"🌐 Dashboard: http://localhost:8000"
    )

    muvaffaqiyat = xabar_yuborish(xabar)
    if muvaffaqiyat:
        _oxirgi_yuborish = hozir
    return muvaffaqiyat
