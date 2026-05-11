"""
Sintetik Havo Sifati Ma'lumotlari Generatori
=============================================
30 kunlik dataset: har 30 sekundda 1 yozuv — jami 86,400 yozuv.

Toshkent shahri iqlimi va havo sifati patternlari asosida:
  - Ertalab (6-9):   transport tiqilishi → AQI yuqori (80-150)
  - Kunduzi (10-17): normal → AQI past-o'rta (40-80)
  - Kechqurun (18-21): traffic → AQI o'rtacha (60-120)
  - Tunda (22-5):    toza havo → AQI past (20-40)

Ishlatish:
    python ml/data_generator.py
"""

import numpy as np
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

# ── Chiqish papkalarini yaratish ──────────────────────────────
ML_DIR   = Path(__file__).parent
DATA_DIR = ML_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Sozlamalar ────────────────────────────────────────────────
BOSHLANISH_VAQT = datetime(2025, 5, 1, 0, 0, 0)   # dataset boshlanishi
INTERVAL_SEK    = 30                                # sekundda bir o'lchov
KUN_SONI        = 30                               # 30 kunlik dataset
YOZUV_SONI      = KUN_SONI * 24 * 3600 // INTERVAL_SEK   # = 86,400
CSV_YOLI        = DATA_DIR / "havo_data.csv"
DB_YOLI         = ML_DIR.parent / "havo_data.db"   # loyiha root


# ═══════════════════════════════════════════════════════════════
# ASOSIY FIZIK MODELLAR
# ═══════════════════════════════════════════════════════════════

def soat_aqi_bazasi(soat: int) -> float:
    """
    Soatga qarab AQI ning asosiy darajasi.
    Toshkent shahri kunlik transport patterti asosida.
    """
    if 6 <= soat < 10:
        return 100.0    # Ertalabki transport tiqilishi
    elif 10 <= soat < 18:
        return 52.0     # Kunduzi — ish vaqti, normal
    elif 18 <= soat < 22:
        return 72.0     # Kechki traffic
    else:
        return 27.0     # Tunda — toza, harakatsiz


def harorat_hisoblash(soat: int, kun_raqami: int) -> float:
    """
    Toshkent yoz harorati (°C).
    Min: ~24°C (05:00 da), Max: ~38°C (14:00 da).
    Mavsumiy o'zgarish: 30 kun ichida ±3°C.
    """
    mavsumiy = 3.0 * np.sin(2 * np.pi * kun_raqami / 30)
    kunlik   = 7.0 * np.sin(np.pi * (soat - 5) / 18)
    return 29.0 + mavsumiy + kunlik


def namlik_hisoblash(harorat: float) -> float:
    """
    Nisbiy namlik (%).
    Harorat oshsa — namlik kamayadi (teskari bog'liq).
    Toshkent: 30-70% oralig'ida.
    """
    base = 68.0 - 1.2 * (harorat - 20.0)
    return float(np.clip(base, 25.0, 75.0))


def bosim_hisoblash(soat: int, kun_raqami: int) -> float:
    """
    Toshkent uchun atmosfera bosimi modeli (hPa).
    Kechasi: ~1015-1025 hPa (radiativ sovish → bosim oshadi).
    Kunduzi: ~1010-1020 hPa (qizish → bosim kamayadi).
    O'rtacha: ~1013 hPa, 10 kunlik mavsumiy tsikl.
    """
    # Kunlik amplituda: max ~03:00 da (kecha), min ~15:00 da (kunduz)
    kunlik   = 5.0 * np.cos(2 * np.pi * (soat - 3) / 24)
    mavsumiy = 4.0 * np.sin(2 * np.pi * kun_raqami / 10)
    return 1013.0 + kunlik + mavsumiy


def aqi_dan_pm25(aqi: int) -> float:
    """AQI qiymatidan PM2.5 taxminiy hisoblash (EPA teskari formula)."""
    if aqi <= 50:
        return aqi * 12.0 / 50.0
    elif aqi <= 100:
        return 12.0 + (aqi - 50) * 23.4 / 50.0
    elif aqi <= 150:
        return 35.4 + (aqi - 100) * 20.0 / 50.0
    else:
        return 55.4 + (aqi - 150) * 3.5


# ═══════════════════════════════════════════════════════════════
# MA'LUMOT YARATISH
# ═══════════════════════════════════════════════════════════════

def yozuvlar_yaratish() -> pd.DataFrame:
    """
    86,400 ta sintetik yozuv yaratish.
    Ba'zi kunlar sun'iy "ifloslanish hodisasi" simulyatsiya qilinadi.
    """
    np.random.seed(42)

    # 5 ta tasodifiy "iflos kun" (sanoat falokati, kuchli chang bo'roni)
    iflos_kunlar = set(np.random.choice(range(KUN_SONI), size=5, replace=False))
    print(f"   Iflos kun simulyatsiyasi: kunlar {sorted(iflos_kunlar)}")

    yozuvlar = []
    vaqt = BOSHLANISH_VAQT

    for _ in range(YOZUV_SONI):
        soat       = vaqt.hour
        kun_raqami = (vaqt - BOSHLANISH_VAQT).days

        # ── Harorat va namlik ──
        harorat = harorat_hisoblash(soat, kun_raqami) + np.random.normal(0, 0.5)
        namlik  = namlik_hisoblash(harorat) + np.random.normal(0, 2.0)

        # ── AQI: asosiy pattern + shovqin + maxsus hodisalar ──
        aqi_base = soat_aqi_bazasi(soat)
        aqi_base += np.random.normal(0, 12.0)       # o'lchov shovqini

        # Iflos kun: AQI 60-100% ga oshadi
        if kun_raqami in iflos_kunlar:
            aqi_base *= np.random.uniform(1.6, 2.0)

        # Ish kunlari (Dush-Juma) biroz yuqoriroq
        if vaqt.weekday() < 5:
            aqi_base *= 1.05

        aqi = int(np.clip(round(aqi_base), 5, 450))

        # ── PM2.5 va PM10 ──
        pm25 = max(0.5, aqi_dan_pm25(aqi) + np.random.normal(0, 1.5))
        pm10 = max(1.0, pm25 * np.random.uniform(1.5, 2.2))

        # ── MQ sensorlari (raqamli DO: 1=toza, 0=gaz aniqlandi) ──
        mq135 = 0 if aqi > 125 else 1   # CO₂, NH₃, Benzol
        mq2   = 0 if aqi > 165 else 1   # Metan, LPG, Tutun
        mq7   = 0 if aqi > 145 else 1   # Uglerod oksidi (CO)

        # ── Atmosfera bosimi: kunlik + mavsumiy model, ±5 hPa og'ish ──
        bosim = bosim_hisoblash(soat, kun_raqami) + np.random.normal(0, 2.5)
        bosim = float(np.clip(bosim, 980.0, 1050.0))

        yozuvlar.append({
            "vaqt":    vaqt.strftime("%Y-%m-%d %H:%M:%S"),
            "harorat": round(float(harorat), 1),
            "namlik":  round(float(np.clip(namlik, 15.0, 90.0)), 1),
            "mq135":   mq135,
            "mq2":     mq2,
            "mq7":     mq7,
            "pm25":    round(float(pm25), 2),
            "pm10":    round(float(pm10), 2),
            "bosim":   round(float(bosim), 1),
            "aqi":     aqi,
        })

        vaqt += timedelta(seconds=INTERVAL_SEK)

    return pd.DataFrame(yozuvlar)


# ═══════════════════════════════════════════════════════════════
# SAQLASH FUNKSIYALARI
# ═══════════════════════════════════════════════════════════════

def csv_saqlash(df: pd.DataFrame) -> None:
    """DataFrame ni CSV formatida saqlash."""
    df.to_csv(CSV_YOLI, index=False, encoding="utf-8")
    print(f"✅ CSV saqlandi: {CSV_YOLI}  ({len(df):,} yozuv)")


def sqlite_saqlash(df: pd.DataFrame) -> None:
    """
    Sintetik ma'lumotlarni SQLite bazaga qo'shish.
    Bazada 1000 dan kam yozuv bo'lsagina qo'shadi.
    """
    if not DB_YOLI.exists():
        print(f"⚠️  {DB_YOLI} topilmadi — SQLite saqlash o'tkazib yuborildi.")
        return

    conn = sqlite3.connect(DB_YOLI)
    mavjud = conn.execute("SELECT COUNT(*) FROM measurements").fetchone()[0]

    if mavjud >= 1000:
        print(f"ℹ️  SQLite: {mavjud:,} yozuv bor, sintetik yozuvlar qo'shilmadi.")
        conn.close()
        return

    df_ins = df.copy()
    df_ins["device_id"] = "esp32_sim"
    cols = ["device_id", "vaqt", "mq135", "mq2", "mq7",
            "harorat", "namlik", "bosim", "pm25", "pm10", "aqi"]
    df_ins[cols].to_sql("measurements", conn, if_exists="append", index=False)
    conn.commit()

    yangi_jami = conn.execute("SELECT COUNT(*) FROM measurements").fetchone()[0]
    conn.close()
    print(f"✅ SQLite bazaga {len(df):,} yozuv qo'shildi (jami: {yangi_jami:,})")


# ═══════════════════════════════════════════════════════════════
# STATISTIKA
# ═══════════════════════════════════════════════════════════════

def statistika_chiqar(df: pd.DataFrame) -> None:
    """Dataset statistikasini chiroyli ko'rsatish."""
    print("\n📊 Dataset statistikasi:")
    print(f"   Yozuvlar soni  : {len(df):,}")
    print(f"   Vaqt oralig'i  : {df['vaqt'].iloc[0]} → {df['vaqt'].iloc[-1]}")
    print(f"   AQI    — o'rta: {df['aqi'].mean():.1f}, min: {df['aqi'].min()}, max: {df['aqi'].max()}")
    print(f"   T°C    — o'rta: {df['harorat'].mean():.1f}, min: {df['harorat'].min():.1f}, max: {df['harorat'].max():.1f}")
    print(f"   Namlik — o'rta: {df['namlik'].mean():.1f}%")
    print(f"   PM2.5  — o'rta: {df['pm25'].mean():.1f} μg/m³")
    print(f"   Bosim  — o'rta: {df['bosim'].mean():.1f} hPa, min: {df['bosim'].min():.1f}, max: {df['bosim'].max():.1f}")

    print("\n   AQI taqsimlanishi:")
    kategoriyalar = [
        ("Yaxshi      (  0-50)", (df["aqi"] <= 50).sum()),
        ("O'rtacha    ( 51-100)", ((df["aqi"] > 50)  & (df["aqi"] <= 100)).sum()),
        ("Sezgir      (101-150)", ((df["aqi"] > 100) & (df["aqi"] <= 150)).sum()),
        ("Zararli     (151-200)", ((df["aqi"] > 150) & (df["aqi"] <= 200)).sum()),
        ("Juda zararli(201+)",    (df["aqi"] > 200).sum()),
    ]
    for nomi, soni in kategoriyalar:
        foiz  = soni / len(df) * 100
        barra = "█" * int(foiz / 2)
        print(f"     {nomi}: {soni:6,} ({foiz:4.1f}%) {barra}")


# ═══════════════════════════════════════════════════════════════
# ASOSIY
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 58)
    print("  Sintetik Havo Sifati Ma'lumotlari Generatori")
    print("=" * 58)
    print(f"  {YOZUV_SONI:,} yozuv | {KUN_SONI} kun | har {INTERVAL_SEK}s")
    print()

    print("🔄 Yozuvlar yaratilmoqda...")
    df = yozuvlar_yaratish()

    csv_saqlash(df)
    sqlite_saqlash(df)
    statistika_chiqar(df)

    print(f"\n✨ Tayyor!")
    print(f"   Keyingi qadam: python ml/train_model.py")
