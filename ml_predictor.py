"""
Havo Sifati Bashorat Moduli — Placeholder

Izoh: Bu modul hozircha statistik usullar bilan ishlaydi.
To'liq LSTM neyron tarmog'i modeli 1-2 hafta ma'lumot to'plangach
ml_training.ipynb faylida yaratiladi (Jupyter Notebook).

Kelajakdagi arxitektura:
    - LSTM (Long Short-Term Memory) — vaqt qatori uchun
    - Input: oxirgi 24 soatlik AQI, sensor qiymatlari
    - Output: keyingi 1 soat uchun AQI bashorat
    - Anomaliya: Isolation Forest yoki Autoencoder
"""
import logging
import statistics

log = logging.getLogger(__name__)


class HavoSifatBashorati:
    """
    Havo sifati bashorat va anomaliya aniqlash sinfi.

    Hozirgi holat: oddiy statistik usullar.
    Kelajak: TensorFlow/Keras LSTM modeli.
    """

    def __init__(self):
        log.info("🤖 Bashorat modeli yuklandi (statistik rejim).")

    def predict_next_hour(self, oxirgi_olchovlar: list[dict]) -> dict:
        """
        Keyingi 1 soatlik AQI bashorati.

        Hozircha: so'nggi 10 ta o'lchovning og'irlikli o'rtachasi.
        Kelajakda: LSTM modeli bashorati.

        Qaytaradi:
            aqi_bashorat — taxminiy AQI qiymati
            ishonch       — bashorat ishonch darajasi (0.0–1.0)
            usul          — ishlatilgan usul nomi
            xabar         — foydalanuvchiga ma'lumot
        """
        if not oxirgi_olchovlar:
            return {
                "aqi_bashorat": None,
                "ishonch": 0.0,
                "usul": "yetarli_malumot_yoq",
                "xabar": "Bashorat uchun yetarli ma'lumot yo'q. Sensor ma'lumotlari kutilmoqda.",
            }

        aqilar = [
            o["aqi"] for o in oxirgi_olchovlar[-12:]
            if o.get("aqi") is not None
        ]

        if len(aqilar) < 2:
            return {
                "aqi_bashorat": None,
                "ishonch": 0.0,
                "usul": "kam_malumot",
                "xabar": f"Faqat {len(aqilar)} ta AQI qiymati mavjud. Kamida 2 ta kerak.",
            }

        # So'nggi qiymatlar ko'proq og'irlikka ega (eksponensial og'irlik)
        og_irliklar = [1.2 ** i for i in range(len(aqilar))]
        jami = sum(og_irliklar)
        bashorat = round(sum(a * w for a, w in zip(aqilar, og_irliklar)) / jami)

        # Ishonch darajasi: qiymatlar barqaror bo'lsa yuqori
        std = statistics.stdev(aqilar) if len(aqilar) > 1 else 0
        ishonch = max(0.3, min(0.82, 1.0 - std / 120))

        return {
            "aqi_bashorat": bashorat,
            "ishonch":      round(ishonch, 2),
            "usul":         "statistik_ogirlikli_orta",
            "xabar":        (
                f"So'nggi {len(aqilar)} ta o'lchovga asoslangan taxmin. "
                "Aniqroq bashorat uchun LSTM modeli tayyorlanmoqda."
            ),
        }

    def detect_anomaly(self, hozirgi: dict, tarix: list[dict]) -> dict:
        """
        Anomaliya aniqlash.

        Hozircha: Z-score statistik chegarasi.
        Kelajakda: Isolation Forest yoki Autoencoder reconstruction error.
        """
        if len(tarix) < 5 or not hozirgi.get("aqi"):
            return {"anomaliya": False, "sabablar": [], "daraja": "normal", "z_ball": 0.0}

        aqilar = [o["aqi"] for o in tarix if o.get("aqi") is not None]
        if len(aqilar) < 3:
            return {"anomaliya": False, "sabablar": [], "daraja": "normal", "z_ball": 0.0}

        orta = statistics.mean(aqilar)
        std  = statistics.stdev(aqilar) if len(aqilar) > 1 else 1.0
        z    = abs(hozirgi["aqi"] - orta) / max(std, 0.001)

        sabablar = []
        if z > 3:
            sabablar.append(
                f"AQI qiymati ({hozirgi['aqi']}) tarixiy o'rtamadan ({orta:.0f}) keskin farqli."
            )
        if hozirgi.get("mq2")   == 0:
            sabablar.append("Yonuvchan gaz aniqlandi (MQ-2 sensori).")
        if hozirgi.get("mq135") == 0:
            sabablar.append("Zararli havo gazi aniqlandi (MQ-135 sensori).")
        if hozirgi.get("mq7")   == 0:
            sabablar.append("Uglerod oksidi (CO) aniqlandi (MQ-7 sensori).")

        return {
            "anomaliya": bool(sabablar) or z > 3,
            "sabablar":  sabablar,
            "daraja":    "yuqori" if z > 3 else ("o'rta" if z > 2 else "normal"),
            "z_ball":    round(z, 2),
        }
