"""
Havo Sifati Monitoringi — Ma'lumotlar bazasi moduli
SQLite bilan barcha CRUD operatsiyalari shu yerda.
"""
import sqlite3
import logging
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager

log = logging.getLogger(__name__)

DB_FAYL     = "havo_data.db"
SAQLASH_KUN = 30
TOSHKENT_TZ = timezone(timedelta(hours=5))


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_FAYL)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def db_yaratish():
    """Jadvallar va indekslarni yaratish (agar mavjud bo'lmasa)."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS measurements (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT    NOT NULL DEFAULT 'esp32_001',
                vaqt      TEXT    NOT NULL,
                mq135     INTEGER,
                mq2       INTEGER,
                mq7       INTEGER,
                harorat   REAL,
                namlik    REAL,
                bosim     REAL,
                pm25      REAL,
                pm10      REAL,
                aqi       INTEGER
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vaqt    ON measurements(vaqt)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_device  ON measurements(device_id)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                vaqt        TEXT NOT NULL,
                sensor_nomi TEXT NOT NULL,
                qiymat      TEXT,
                xabar       TEXT NOT NULL
            )
        """)
        conn.commit()
    log.info("✅ Ma'lumotlar bazasi tayyor: %s", DB_FAYL)


def malumot_saqlash(data: dict) -> int:
    """Yangi o'lchov yozuvini bazaga saqlash. ID ni qaytaradi."""
    vaqt = datetime.now(TOSHKENT_TZ).isoformat()
    with get_db() as conn:
        cur = conn.execute("""
            INSERT INTO measurements
                (device_id, vaqt, mq135, mq2, mq7, harorat, namlik, bosim, pm25, pm10, aqi)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("device_id", "esp32_001"), vaqt,
            data.get("mq135"), data.get("mq2"),   data.get("mq7"),
            data.get("harorat"), data.get("namlik"), data.get("bosim"),
            data.get("pm25"),   data.get("pm10"),   data.get("aqi"),
        ))
        conn.commit()
        return cur.lastrowid


def oxirgi_olchov() -> dict | None:
    """Eng so'nggi o'lchov yozuvini olish."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM measurements ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return dict(row) if row else None


def vaqt_oraligi_malumotlar(soat: int = 1) -> list[dict]:
    """Berilgan soat oralig'idagi yozuvlar (grafik uchun, vaqt bo'yicha o'sish tartibida)."""
    chegara = (datetime.now(TOSHKENT_TZ) - timedelta(hours=soat)).isoformat()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM measurements WHERE vaqt >= ? ORDER BY vaqt ASC",
            (chegara,)
        ).fetchall()
    return [dict(r) for r in rows]


def jadval_malumotlar(limit: int = 50, offset: int = 0) -> list[dict]:
    """Jadval uchun so'nggi yozuvlar (sahifalash bilan)."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM measurements ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
    return [dict(r) for r in rows]


def statistika(soat: int = 24) -> dict:
    """Berilgan vaqt oralig'i uchun statistika (o'rtacha, max, min)."""
    chegara = (datetime.now(TOSHKENT_TZ) - timedelta(hours=soat)).isoformat()
    with get_db() as conn:
        row = conn.execute("""
            SELECT
                COUNT(*)      AS jami,
                AVG(aqi)      AS orta_aqi,
                MAX(aqi)      AS max_aqi,
                MIN(aqi)      AS min_aqi,
                AVG(harorat)  AS orta_harorat,
                AVG(namlik)   AS orta_namlik,
                AVG(bosim)    AS orta_bosim,
                AVG(pm25)     AS orta_pm25,
                AVG(pm10)     AS orta_pm10
            FROM measurements WHERE vaqt >= ?
        """, (chegara,)).fetchone()
        jami_baza = conn.execute("SELECT COUNT(*) FROM measurements").fetchone()[0]

    def r2(v):
        return round(v, 1) if v is not None else None

    return {
        "vaqt_oraligi_soat": soat,
        "olchov_soni":        row["jami"],
        "jami_baza":          jami_baza,
        "aqi":      {"orta": r2(row["orta_aqi"]),     "max": row["max_aqi"], "min": row["min_aqi"]},
        "harorat":  {"orta": r2(row["orta_harorat"])},
        "namlik":   {"orta": r2(row["orta_namlik"])},
        "bosim":    {"orta": r2(row["orta_bosim"])},
        "pm25":     {"orta": r2(row["orta_pm25"])},
        "pm10":     {"orta": r2(row["orta_pm10"])},
    }


def eski_malumot_tozalash():
    """30 kundan eski yozuvlarni o'chirish."""
    chegara = (datetime.now(TOSHKENT_TZ) - timedelta(days=SAQLASH_KUN)).isoformat()
    with get_db() as conn:
        cur = conn.execute("DELETE FROM measurements WHERE vaqt < ?", (chegara,))
        conn.commit()
        if cur.rowcount:
            log.info("🧹 %d ta eski yozuv o'chirildi.", cur.rowcount)


def ogohlantirish_saqlash(sensor_nomi: str, qiymat: str, xabar: str):
    """Ogohlantirish yozuvini bazaga saqlash."""
    vaqt = datetime.now(TOSHKENT_TZ).isoformat()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO alerts (vaqt, sensor_nomi, qiymat, xabar) VALUES (?, ?, ?, ?)",
            (vaqt, sensor_nomi, qiymat, xabar)
        )
        conn.commit()
