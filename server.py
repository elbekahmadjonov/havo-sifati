"""
Havo Sifati Monitoringi — Asosiy FastAPI Server v2.0
Diplom ishi: "Havo sifatining bashoratli monitoringi uchun aqlli qurilma va dasturiy ta'minot"
"""
import io
import csv
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

import database
import aqi_calculator
import ml_predictor
import telegram_alert

# ─── Logging sozlamasi ───
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("logs/server.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

TOSHKENT_TZ = timezone(timedelta(hours=5))


def _vaqt_farq_matn(vaqt_str: str | None) -> str:
    """Oxirgi o'lchov vaqtidan qancha o'tganligini o'zbek tilida qaytaradi."""
    if not vaqt_str:
        return "Noma'lum"
    try:
        delta  = datetime.now(TOSHKENT_TZ) - datetime.fromisoformat(vaqt_str)
        daqiqa = int(delta.total_seconds() / 60)
        soat   = daqiqa // 60
        if soat > 0:
            return f"{soat} soat {daqiqa % 60} daqiqa oldin"
        return f"{max(daqiqa, 0)} daqiqa oldin"
    except Exception:
        return "Noma'lum"

# ─── ML bashorat modeli ───
bashorat_modeli = ml_predictor.HavoSifatBashorati()


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.db_yaratish()
    log.info("🚀 Server muvaffaqiyatli ishga tushdi!")
    log.info("📡 ESP32 -> POST /api/sensor")
    log.info("🌐 Dashboard -> http://localhost:8000")
    yield
    log.info("🛑 Server to'xtatildi.")


app = FastAPI(
    title="Havo Sifati Monitoringi",
    description="ESP32 + MQ-135/MQ-2 asosida real vaqt havo sifati monitoringi",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


# ─── Pydantic modeli — ESP32 yuboradigan JSON ───
class SensorMalumot(BaseModel):
    device_id: str           = "esp32_001"
    mq135:     Optional[int]   = None
    mq2:       Optional[int]   = None
    mq7:       Optional[int]   = None
    harorat:   Optional[float] = None
    namlik:    Optional[float] = None
    bosim:     Optional[float] = None
    pm25:      Optional[float] = None
    pm10:      Optional[float] = None


# ═══════════════════════════════════════════════════
# API ENDPOINTLAR
# ═══════════════════════════════════════════════════

@app.post("/api/sensor", summary="ESP32 dan sensor ma'lumotlari qabul qilish")
async def sensor_qabul(m: SensorMalumot):
    """
    ESP32 har 30 sekundda shu endpointga JSON POST yuboradi.
    Null qiymatlar — sensor hali ulanmagan degani.
    """
    data = m.model_dump()

    # AQI hisoblash
    aqi      = aqi_calculator.get_overall_aqi(data)
    data["aqi"] = aqi
    kat      = aqi_calculator.get_aqi_category(aqi)

    # Bazaga saqlash
    yozuv_id = database.malumot_saqlash(data)

    # Telegram ogohlantirish (agar kerak bo'lsa)
    sensor_holat = {k: data.get(k) for k in ("mq135", "mq2", "mq7", "pm25", "pm10", "harorat")}
    telegram_alert.aqi_tekshir_va_xabarlash(aqi, kat["daraja"], sensor_holat)

    # Har 200 ta yozuvda eski ma'lumotlarni tozalash
    if yozuv_id % 200 == 0:
        database.eski_malumot_tozalash()

    log.info("📥 ID:%-4d | AQI:%-3d (%s) | %s", yozuv_id, aqi, kat["daraja"], m.device_id)

    return {
        "status":  "ok",
        "id":      yozuv_id,
        "aqi":     aqi,
        "daraja":  kat["daraja"],
        "vaqt":    datetime.now(TOSHKENT_TZ).isoformat(),
    }


@app.get("/api/data", summary="Sensor ma'lumotlari (jadval + grafik)")
async def api_data(
    limit:  int = Query(50,  ge=1,  le=500),
    soat:   int = Query(1,   ge=1,  le=720),
    offset: int = Query(0,   ge=0),
):
    """
    soat  — grafik uchun qancha soatlik ma'lumot (1, 24, 168, 720)
    limit — jadval uchun yozuvlar soni
    """
    grafik = database.vaqt_oraligi_malumotlar(soat)
    jadval = database.jadval_malumotlar(limit, offset)
    oxirgi = database.oxirgi_olchov()

    return {
        "oxirgi":     oxirgi,
        "grafik":     grafik,
        "jadval":     jadval,
        "jami":       database.statistika(soat)["olchov_soni"],
        "server_vaqt": datetime.now(TOSHKENT_TZ).isoformat(),
    }


@app.get("/api/aqi", summary="Hozirgi AQI qiymati va holati")
async def api_aqi():
    """Eng so'nggi o'lchovdan hisoblangan AQI, daraja, sensor holati va sog'liq tavsiyasi."""
    oxirgi          = database.oxirgi_olchov()
    online          = database.qurilma_onlinemi()
    oxirgi_vaqt_str = oxirgi.get("vaqt") if oxirgi else None
    oxirgi_korinish = _vaqt_farq_matn(oxirgi_vaqt_str)

    if not oxirgi or not online:
        return {
            "hozir":           None,
            "daraja":          "Noma'lum",
            "rang":            "#64748b",
            "emoji":           "⚫",
            "tavsiya":         "Qurilma bilan aloqa yo'q! So'nggi ma'lumot yangilanmayapti.",
            "sensorlar":       [],
            "harorat":         None,
            "namlik":          None,
            "oxirgi_vaqt":     oxirgi_vaqt_str,
            "qurilma_online":  False,
            "oxirgi_korinish": oxirgi_korinish,
        }

    aqi     = oxirgi.get("aqi") or aqi_calculator.get_overall_aqi(oxirgi)
    kat     = aqi_calculator.get_aqi_category(aqi)
    tavsiya = aqi_calculator.sog_liq_tavsiya(
        aqi,
        harorat=oxirgi.get("harorat"),
        namlik=oxirgi.get("namlik"),
    )
    sensorlar = aqi_calculator.sensor_holati(
        mq135=oxirgi.get("mq135"),
        mq2=oxirgi.get("mq2"),
        mq7=oxirgi.get("mq7"),
    )

    return {
        "hozir":           kat["aqi"],
        "daraja":          kat["daraja"],
        "rang":            kat["rang"],
        "emoji":           kat.get("emoji", ""),
        "tavsiya":         tavsiya,
        "sensorlar":       sensorlar,
        "harorat":         oxirgi.get("harorat"),
        "namlik":          oxirgi.get("namlik"),
        "bosim":           oxirgi.get("bosim"),
        "oxirgi_vaqt":     oxirgi.get("vaqt"),
        "qurilma_online":  True,
        "oxirgi_korinish": oxirgi_korinish,
    }


@app.get("/api/predict", summary="Keyingi 1 soatlik AQI bashorati")
async def api_predict():
    """So'nggi 3 soatlik ma'lumot asosida AQI bashorati (ML placeholder)."""
    tarix  = database.vaqt_oraligi_malumotlar(soat=3)
    natija = bashorat_modeli.predict_next_hour(tarix)

    if natija.get("aqi_bashorat") is not None:
        kat            = aqi_calculator.get_aqi_category(natija["aqi_bashorat"])
        natija["daraja"] = kat["daraja"]
        natija["rang"]   = kat["rang"]

    return natija


@app.get("/api/stats", summary="Statistika (o'rtacha, max, min)")
async def api_stats(soat: int = Query(24, ge=1, le=720)):
    """Berilgan vaqt oralig'i uchun statistik ma'lumotlar."""
    return database.statistika(soat)


@app.get("/api/export/csv", summary="Barcha ma'lumotlarni CSV yuklab olish")
async def api_export_csv():
    """ML model o'qitish uchun to'liq dataset CSV sifatida yuklab olinadi."""
    barcha = database.jadval_malumotlar(limit=100_000)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "id", "device_id", "vaqt", "mq135", "mq2", "mq7",
        "harorat", "namlik", "bosim", "pm25", "pm10", "aqi",
    ])
    writer.writeheader()
    writer.writerows(barcha)
    output.seek(0)

    fayl_nomi = f"havo_data_{datetime.now(TOSHKENT_TZ).strftime('%Y%m%d_%H%M%S')}.csv"
    log.info("📤 CSV eksport: %s (%d yozuv)", fayl_nomi, len(barcha))

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={fayl_nomi}"},
    )


# ═══════════════════════════════════════════════════
# HTML SAHIFALAR (Jinja2 ishlatilmaydi — Python 3.14 muammosi)
# ═══════════════════════════════════════════════════

@app.get("/", summary="Asosiy dashboard sahifasi")
async def sahifa_asosiy():
    return FileResponse("templates/index.html")


@app.get("/history", summary="Tarix va grafiklar sahifasi")
async def sahifa_tarix():
    return FileResponse("templates/history.html")


@app.get("/about", summary="Loyiha haqida sahifa")
async def sahifa_haqida():
    return FileResponse("templates/about.html")


# ─── To'g'ridan-to'g'ri ishga tushirish ───
if __name__ == "__main__":
    print("=" * 55)
    print("  Havo Sifati Monitoringi — v2.0")
    print("  Diplom ishi, 2025")
    print("=" * 55)
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
