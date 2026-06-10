import logging
import statistics

log = logging.getLogger(__name__)

_lstm_bashorat = None
_lstm_faol     = False

try:
    from ml.predictor import HavoBashorati as _HavoBashorati
    _lstm_bashorat = _HavoBashorati()
    _lstm_faol     = _lstm_bashorat.model is not None

    if _lstm_faol:
        log.info("LSTM model faol")
    else:
        log.info("LSTM model topilmadi, statistik rejim. "
                 "O'rgatish: python ml/train_model.py")

except ImportError:
    log.info("ml.predictor topilmadi, statistik rejim.")
except Exception as exc:
    log.warning("ML xato (%s), statistik rejim.", exc)

class HavoSifatBashorati:

    def __init__(self):
        self._ml   = _lstm_bashorat
        self._faol = _lstm_faol
        rejim = "LSTM neyron tarmog'i" if self._faol else "Statistik (zaxira)"
        log.info("bashorat rejimi: %s", rejim)

    def predict_next_hour(self, oxirgi_olchovlar: list[dict]) -> dict:
        if self._faol and len(oxirgi_olchovlar) >= 5:
            return self._ml.predict_next_hour(oxirgi_olchovlar)
        return self._statistik_bashorat(oxirgi_olchovlar)

    def detect_anomaly(self, hozirgi: dict, tarix: list[dict]) -> dict:
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
                f"AQI ({hozirgi['aqi']}) tarixiy o'rtamadan ({orta:.0f}) keskin farqli."
            )
        if hozirgi.get("mq2")   == 0: sabablar.append("Yonuvchan gaz aniqlandi (MQ-2).")
        if hozirgi.get("mq135") == 0: sabablar.append("Zararli gaz aniqlandi (MQ-135).")
        if hozirgi.get("mq7")   == 0: sabablar.append("CO aniqlandi (MQ-7).")

        return {
            "anomaliya": bool(sabablar) or z > 3,
            "sabablar":  sabablar,
            "daraja":    "yuqori" if z > 3 else ("o'rta" if z > 2 else "normal"),
            "z_ball":    round(z, 2),
        }

    def _statistik_bashorat(self, olchovlar: list[dict]) -> dict:
        if not olchovlar:
            return {
                "aqi_bashorat": None, "ishonch": 0.0,
                "usul":  "yetarli_malumot_yoq",
                "xabar": "Bashorat uchun yetarli ma'lumot yo'q. Sensor ma'lumotlari kutilmoqda.",
            }

        aqilar = [o["aqi"] for o in olchovlar[-12:] if o.get("aqi") is not None]

        if len(aqilar) < 2:
            return {
                "aqi_bashorat": None, "ishonch": 0.0,
                "usul":  "kam_malumot",
                "xabar": f"Faqat {len(aqilar)} ta AQI qiymati. Kamida 2 ta kerak.",
            }

        og_irliklar = [1.2 ** i for i in range(len(aqilar))]
        bashorat    = round(sum(a * w for a, w in zip(aqilar, og_irliklar)) / sum(og_irliklar))
        std         = statistics.stdev(aqilar) if len(aqilar) > 1 else 0
        ishonch     = round(max(0.3, min(0.75, 1.0 - std / 120)), 2)

        return {
            "aqi_bashorat": bashorat,
            "ishonch":      ishonch,
            "usul":         "statistik_ogirlikli_orta",
            "xabar":        (
                f"So'nggi {len(aqilar)} ta o'lchovga asoslangan statistik bashorat. "
                "LSTM aniqroq natija uchun: python ml/train_model.py"
            ),
        }
