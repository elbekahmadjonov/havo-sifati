"""
Havo Sifati Bashorat Klasi — PyTorch LSTM model interfeysi
===========================================================
O'rgatilgan model asosida real vaqt AQI bashorati.

Ishlatish:
    from ml.predictor import HavoBashorati
    b = HavoBashorati()
    natija = b.predict_next_hour(last_24_olchovlar)
"""

import logging
import numpy as np
import joblib
from pathlib import Path

log = logging.getLogger(__name__)

# ── Yo'llar ──────────────────────────────────────────────────
_ML_DIR     = Path(__file__).parent
MODEL_YOLI  = _ML_DIR / "models" / "lstm_model.pth"
SCALER_YOLI = _ML_DIR / "models" / "scaler.pkl"

# ── Sozlamalar ────────────────────────────────────────────────
FEATURES    = ["harorat", "namlik", "mq135", "mq2", "mq7", "aqi"]
VAQT_QADAMI = 24

# ── AQI darajalari ────────────────────────────────────────────
_AQI_DARAJALARI = [
    (0,   50,  "Yaxshi",                      "#10b981", "🟢"),
    (51,  100, "O'rtacha",                    "#f59e0b", "🟡"),
    (101, 150, "Sezgir guruh uchun zararli",  "#f97316", "🟠"),
    (151, 200, "Zararli",                     "#ef4444", "🔴"),
    (201, 300, "Juda zararli",                "#8b5cf6", "🟣"),
    (301, 500, "Xavfli",                      "#78350f", "⚫"),
]

# ── O'zbek tilidagi tavsiyalar ────────────────────────────────
_AQI_TAVSIYALAR = [
    (0,   50,  "Havo a'lo! Tashqarida sport va faol hayot kechirish mumkin. 🌿"),
    (51,  100, "Havo qoniqarli. Sezgir odamlar uzoq muddatli mashqlarni cheklashi tavsiya etiladi. 😊"),
    (101, 150, "Bolalar, keksalar va nafas kasalligi bor kishilar tashqari faoliyatini qisqartirsin. ⚠️"),
    (151, 200, "Barcha odamlar tashqi faoliyatni kamaytirsin. Sezgir guruhlar ichkarida qolsin! 🚨"),
    (201, 300, "Sog'liq uchun favqulodda holat! Niqob kiyish va ichkarida qolish tavsiya etiladi. 🆘"),
    (301, 500, "O'ta jiddiy xavf! Tashqarida mutlaqo bo'lmang. Tibbiy yordam oling. ☠️"),
]


# ═══════════════════════════════════════════════════════════════
# PYTORCH MODEL ARXITEKTURASI (train_model.py bilan bir xil)
# ═══════════════════════════════════════════════════════════════

def _model_arxitekturasi():
    """PyTorch import va LSTMModel klassi."""
    import torch
    import torch.nn as nn

    class LSTMModel(nn.Module):
        def __init__(self, input_size=6, hidden1=64, hidden2=32, dropout=0.2):
            super().__init__()
            self.lstm1 = nn.LSTM(input_size, hidden1, batch_first=True)
            self.drop1 = nn.Dropout(dropout)
            self.lstm2 = nn.LSTM(hidden1, hidden2, batch_first=True)
            self.drop2 = nn.Dropout(dropout)
            self.fc1   = nn.Linear(hidden2, 16)
            self.relu  = nn.ReLU()
            self.fc2   = nn.Linear(16, 1)

        def forward(self, x):
            out, _ = self.lstm1(x)
            out    = self.drop1(out)
            out, _ = self.lstm2(out)
            out    = self.drop2(out[:, -1, :])
            out    = self.relu(self.fc1(out))
            return self.fc2(out)

    return torch, LSTMModel


# ═══════════════════════════════════════════════════════════════
# YORDAMCHI FUNKSIYALAR
# ═══════════════════════════════════════════════════════════════

def _daraja_info(aqi: int) -> dict:
    for lo, hi, daraja, rang, emoji in _AQI_DARAJALARI:
        if lo <= aqi <= hi:
            return {"daraja": daraja, "rang": rang, "emoji": emoji}
    return {"daraja": "Noma'lum", "rang": "#64748b", "emoji": "❓"}


def get_recommendation(aqi: int) -> str:
    """AQI qiymatiga qarab o'zbek tilidagi tavsiya."""
    for lo, hi, tavsiya in _AQI_TAVSIYALAR:
        if lo <= aqi <= hi:
            return tavsiya
    return "Havo sifati o'ta xavfli! Zudlik bilan xavfsiz joyga o'ting. ☠️"


def _teskari_masshtablash(y_skalyangan: float, scaler) -> float:
    """Skalyangan AQI qiymatini original AQI birligigiga qaytarish."""
    aqi_i       = FEATURES.index("aqi")
    temp        = np.zeros((1, len(FEATURES)), dtype=np.float32)
    temp[0, aqi_i] = y_skalyangan
    return float(scaler.inverse_transform(temp)[0, aqi_i])


# ═══════════════════════════════════════════════════════════════
# ASOSIY KLASS
# ═══════════════════════════════════════════════════════════════

class HavoBashorati:
    """
    LSTM model asosida havo sifati AQI bashorati.

    Metodlar:
        load_model()                 → modelni qayta yuklash
        predict_next_hour(olchovlar) → keyingi AQI bashorati
        predict_trend(olchovlar)     → tendensiya ("yaxshilanadi" / ...)
        get_recommendation(aqi)      → o'zbek tilidagi tavsiya
    """

    def __init__(self):
        self.model  = None
        self.scaler = None
        self._torch = None
        self.load_model()

    def load_model(self) -> bool:
        """
        Diskdan PyTorch modeli va scalerni yuklash.
        Muvaffaqiyatli yuklansa True, aks holda False qaytaradi.
        """
        try:
            torch, LSTMModel = _model_arxitekturasi()
            self._torch = torch

            checkpoint = torch.load(str(MODEL_YOLI), map_location="cpu",
                                    weights_only=False)
            mdl = LSTMModel(
                input_size=checkpoint.get("input_size", len(FEATURES)),
                hidden1=checkpoint.get("hidden1", 64),
                hidden2=checkpoint.get("hidden2", 32),
                dropout=checkpoint.get("dropout", 0.2),
            )
            mdl.load_state_dict(checkpoint["model_state_dict"])
            mdl.eval()
            self.model  = mdl
            self.scaler = joblib.load(str(SCALER_YOLI))

            m = checkpoint.get("metrikalar", {})
            log.info(
                "✅ LSTM modeli yuklandi | MAE=%.2f RMSE=%.2f R²=%.4f",
                m.get("MAE", 0), m.get("RMSE", 0), m.get("R2", 0),
            )
            return True

        except FileNotFoundError:
            log.warning("⚠️  Model topilmadi: %s — avval train_model.py ni ishga tushiring.", MODEL_YOLI)
        except Exception as exc:
            log.error("❌ Model yuklanmadi: %s", exc)
        return False

    def _dict_listdan_massiv(self, olchovlar: list) -> np.ndarray:
        """List[dict] → np.ndarray (n, len(FEATURES))."""
        qatorlar = []
        for m in olchovlar:
            qatorlar.append([
                m.get("harorat") if m.get("harorat") is not None else 28.0,
                m.get("namlik")  if m.get("namlik")  is not None else 50.0,
                m.get("mq135")   if m.get("mq135")   is not None else 1,
                m.get("mq2")     if m.get("mq2")     is not None else 1,
                m.get("mq7")     if m.get("mq7")     is not None else 1,
                m.get("aqi")     if m.get("aqi")     is not None else 50,
            ])
        return np.array(qatorlar, dtype=np.float32)

    def predict_next_hour(self, last_24_olchovlar: list) -> dict:
        """
        Keyingi 1 soatlik AQI bashorati.

        Parametrlar:
            last_24_olchovlar: list[dict] — oxirgi o'lchovlar
                               (ideal: 24 soatlik, kamida 5 ta)
        """
        if self.model is None:
            return self._statistik_bashorat(last_24_olchovlar)

        if len(last_24_olchovlar) < 5:
            return {
                "aqi_bashorat": None, "ishonch": 0.0,
                "usul":  "yetarli_malumot_yoq",
                "xabar": f"Kamida 5 ta o'lchov kerak (hozir {len(last_24_olchovlar)} ta).",
            }

        try:
            arr = self._dict_listdan_massiv(last_24_olchovlar[-VAQT_QADAMI:])

            # Vaqt qadamini to'ldirish (yetarlicha yozuv bo'lmasa)
            if len(arr) < VAQT_QADAMI:
                pad = np.tile(arr[0], (VAQT_QADAMI - len(arr), 1))
                arr = np.vstack([pad, arr])

            arr_scaled = self.scaler.transform(arr)
            X = self._torch.tensor(arr_scaled).unsqueeze(0)   # (1, 24, 6)

            with self._torch.no_grad():
                y_scaled = float(self.model(X).item())

            aqi_pred = int(np.clip(round(_teskari_masshtablash(y_scaled, self.scaler)), 0, 500))
            info     = _daraja_info(aqi_pred)

            return {
                "aqi_bashorat": aqi_pred,
                "ishonch":      0.87,
                "usul":         "lstm_neyron_tarmogi",
                "daraja":       info["daraja"],
                "rang":         info["rang"],
                "xabar":        (
                    f"LSTM bashorati: keyingi soatda AQI ≈ {aqi_pred} "
                    f"({info['daraja']}) {info['emoji']}"
                ),
                "tavsiya":      get_recommendation(aqi_pred),
            }

        except Exception as exc:
            log.error("predict_next_hour xatosi: %s", exc)
            return self._statistik_bashorat(last_24_olchovlar)

    def predict_trend(self, olchovlar: list) -> str:
        """
        AQI tendensiyasini aniqlash.
        Qaytaradi: "yaxshilanadi" | "yomonlashadi" | "barqaror"
        """
        aqilar = [m["aqi"] for m in olchovlar if m.get("aqi") is not None]
        if len(aqilar) < 4:
            return "barqaror"

        yarim    = len(aqilar) // 2
        birinchi = sum(aqilar[:yarim]) / yarim
        ikkinchi = sum(aqilar[yarim:]) / (len(aqilar) - yarim)

        if ikkinchi - birinchi > 10:
            return "yomonlashadi"
        elif birinchi - ikkinchi > 10:
            return "yaxshilanadi"
        return "barqaror"

    def _statistik_bashorat(self, olchovlar: list) -> dict:
        """Eksponensial og'irlikli o'rtacha — zaxira usul."""
        import statistics

        aqilar = [m["aqi"] for m in (olchovlar or [])[-12:] if m.get("aqi") is not None]

        if len(aqilar) < 2:
            return {
                "aqi_bashorat": None, "ishonch": 0.0,
                "usul": "kam_malumot",
                "xabar": "Yetarli ma'lumot yo'q. LSTM model ham yuklanmagan.",
            }

        og_irliklar = [1.2 ** i for i in range(len(aqilar))]
        bashorat    = int(round(sum(a * w for a, w in zip(aqilar, og_irliklar)) / sum(og_irliklar)))
        ishonch     = round(max(0.3, min(0.72, 1.0 - statistics.stdev(aqilar) / 120)), 2)
        info        = _daraja_info(bashorat)

        return {
            "aqi_bashorat": bashorat,
            "ishonch":      ishonch,
            "usul":         "statistik_ogirlikli_orta",
            "daraja":       info["daraja"],
            "rang":         info["rang"],
            "xabar":        (
                f"Statistik bashorat: AQI ≈ {bashorat} ({info['daraja']}). "
                "LSTM aniqroq natija uchun: python ml/train_model.py"
            ),
            "tavsiya":      get_recommendation(bashorat),
        }
