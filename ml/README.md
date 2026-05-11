# Havo Sifati — LSTM Bashorat Moduli

Diplom ishi: "Havo sifatining bashoratli monitoringi uchun aqlli qurilma"

---

## Model Arxitekturasi

```
Kirish (24 soat × 6 xususiyat)
        ↓
LSTM(64 neyron, return_sequences=True)
        ↓
Dropout(0.2)
        ↓
LSTM(32 neyron)
        ↓
Dropout(0.2)
        ↓
Dense(16, ReLU)
        ↓
Dense(1)  ← Keyingi soat AQI bashorati
```

**Kirish xususiyatlari:** `harorat`, `namlik`, `mq135`, `mq2`, `mq7`, `aqi`  
**Vaqt oynasi:** oxirgi 24 soat (soatlik o'rtachalar)  
**Chiqish:** keyingi 1 soat uchun AQI qiymati  
**Yo'qotish funksiyasi:** Huber (outlier larga chidamli)  
**Optimizer:** Adam (lr=0.001, ReduceLROnPlateau bilan)

---

## Fayl Strukturasi

```
ml/
├── __init__.py
├── data_generator.py     ← Sintetik 30 kunlik dataset yaratish
├── train_model.py        ← LSTM o'rgatish va baholash
├── predictor.py          ← Real vaqt bashorat klasi
├── data/
│   └── havo_data.csv     ← 86,400 yozuv (har 30s)
├── models/
│   ├── lstm_model.keras  ← O'rgatilgan model
│   └── scaler.pkl        ← MinMaxScaler
└── results/
    └── training_results.png  ← Loss va bashorat grafiklari
```

---

## O'rgatish Natijalari

| Ko'rsatkich | Ma'no                        | Maqsad   |
|-------------|------------------------------|----------|
| MAE         | O'rtacha absolut xato (AQI)  | < 15     |
| RMSE        | Kvadrat xato ildizi (AQI)    | < 20     |
| R²          | Determinatsiya koeffitsienti | > 0.80   |

---

## Qanday Ishlatish

### 1. Paketlarni o'rnatish

```bash
pip install tensorflow scikit-learn pandas numpy matplotlib joblib
```

### 2. Sintetik ma'lumot yaratish

```bash
python ml/data_generator.py
```

Natija: `ml/data/havo_data.csv` (86,400 yozuv, 30 kun)

### 3. Modelni o'rgatish

```bash
python ml/train_model.py
```

Natijalar:
- `ml/models/lstm_model.keras` — saqlangan model
- `ml/models/scaler.pkl` — masshtablovchi
- `ml/results/training_results.png` — grafiklar

### 4. Server bilan ishlatish

```bash
python server.py
```

LSTM model avtomatik yuklanadi. `GET /api/predict` endpointi bashorat qaytaradi.

### 5. Python da to'g'ridan-to'g'ri ishlatish

```python
from ml.predictor import HavoBashorati

b = HavoBashorati()

# Oxirgi o'lchovlar (real bazadan yoki sintetik)
olchovlar = [
    {"harorat": 32.5, "namlik": 45.0, "mq135": 1, "mq2": 1, "mq7": 1, "aqi": 65},
    # ... (kamida 5 ta, ideali 24 ta)
]

natija = b.predict_next_hour(olchovlar)
print(natija["aqi_bashorat"])   # → 68
print(natija["daraja"])         # → "O'rtacha"
print(natija["tavsiya"])        # → "Havo qoniqarli..."

trend = b.predict_trend(olchovlar)
print(trend)                    # → "yaxshilanadi" | "yomonlashadi" | "barqaror"
```

---

## Muhim Eslatmalar

- **Python versiyasi:** TensorFlow 2.16+ Python 3.9–3.12 ni qo'llaydi.
  Python 3.14 uchun muqobil: `pip install tf-nightly` yoki PyTorch ishlatish.
- **GPU:** NVIDIA GPU bo'lsa `tensorflow-gpu` o'rnating — o'rgatish ~10x tezlashadi.
- **Real ma'lumot:** 30+ kunlik haqiqiy ESP32 ma'lumotlari to'plangach qayta o'rgating.
- **EarlyStopping:** Model overfitting bo'lmaydi — eng yaxshi epoch saqlanadi.
