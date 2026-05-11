"""
LSTM Model O'rgatish — Havo Sifati AQI Bashorati (PyTorch)
===========================================================
Arxitektura:
    Input (24 soat × 6 xususiyat)
    → LSTM(64, return_sequences=True)
    → Dropout(0.2)
    → LSTM(32)
    → Dropout(0.2)
    → Linear(16, ReLU)
    → Linear(1)  ← bashorat qilingan AQI

Ishlatish:
    python ml/train_model.py
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # GUI yo'q serverlarda ishlashi uchun
import matplotlib.pyplot as plt

import joblib
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

print(f"✅ PyTorch {torch.__version__} yuklandi")

# ── Yo'llar ──────────────────────────────────────────────────
ML_DIR      = Path(__file__).parent
CSV_YOLI    = ML_DIR / "data"    / "havo_data.csv"
MODEL_YOLI  = ML_DIR / "models"  / "lstm_model.pth"
SCALER_YOLI = ML_DIR / "models"  / "scaler.pkl"
GRAFIK_YOLI = ML_DIR / "results" / "training_results.png"

(ML_DIR / "models").mkdir(parents=True, exist_ok=True)
(ML_DIR / "results").mkdir(parents=True, exist_ok=True)

# ── Sozlamalar ────────────────────────────────────────────────
VAQT_QADAMI   = 24          # Oxirgi 24 soat → keyingi 1 soat
FEATURES      = ["harorat", "namlik", "mq135", "mq2", "mq7", "aqi"]
TARGET        = "aqi"
TRAIN_NISBATI = 0.80
EPOCHS        = 100
BATCH_SIZE    = 32
LEARNING_RATE = 0.001
PATIENCE      = 12           # EarlyStopping uchun
DEVICE        = "cpu"        # GPU bo'lsa "cuda" qiling


# ═══════════════════════════════════════════════════════════════
# MODEL ARXITEKTURASI
# ═══════════════════════════════════════════════════════════════

class LSTMModel(nn.Module):
    """
    2 qatlamli LSTM neyron tarmog'i.
    Kirish: (batch, vaqt_qadami, xususiyatlar)
    Chiqish: (batch, 1) — AQI bashorati
    """

    def __init__(self, input_size: int = 6, hidden1: int = 64,
                 hidden2: int = 32, dropout: float = 0.2):
        super().__init__()
        self.lstm1  = nn.LSTM(input_size, hidden1, batch_first=True)
        self.drop1  = nn.Dropout(dropout)
        self.lstm2  = nn.LSTM(hidden1, hidden2, batch_first=True)
        self.drop2  = nn.Dropout(dropout)
        self.fc1    = nn.Linear(hidden2, 16)
        self.relu   = nn.ReLU()
        self.fc2    = nn.Linear(16, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm1(x)
        out    = self.drop1(out)
        out, _ = self.lstm2(out)
        out    = self.drop2(out[:, -1, :])   # faqat oxirgi vaqt qadami
        out    = self.relu(self.fc1(out))
        return self.fc2(out)


# ═══════════════════════════════════════════════════════════════
# MA'LUMOT TAYYORLASH
# ═══════════════════════════════════════════════════════════════

def csv_yuklash() -> pd.DataFrame:
    """CSV yuklab, soatlik o'rtachalarga resample qilish."""
    if not CSV_YOLI.exists():
        print(f"❌ CSV topilmadi: {CSV_YOLI}")
        print("   Avval: python ml/data_generator.py")
        sys.exit(1)

    print(f"📂 CSV yuklanmoqda: {CSV_YOLI}")
    df = pd.read_csv(CSV_YOLI, parse_dates=["vaqt"])
    df = df.set_index("vaqt").sort_index()

    # Soatlik o'rtachalar: 86,400 → 720 yozuv
    df_soatlik = df[FEATURES].resample("1h").mean().dropna()

    print(f"   Xom yozuvlar     : {len(df):,}")
    print(f"   Soatlik yozuvlar : {len(df_soatlik)}")
    return df_soatlik


def ketma_ketlik_yaratish(
    skalyangan: np.ndarray, vaqt_qadami: int
) -> tuple[np.ndarray, np.ndarray]:
    """X[i] = skalyangan[i:i+vaqt_qadami]  →  y[i] = AQI[i+vaqt_qadami]"""
    X, y = [], []
    aqi_i = FEATURES.index(TARGET)
    for i in range(len(skalyangan) - vaqt_qadami):
        X.append(skalyangan[i : i + vaqt_qadami])
        y.append(skalyangan[i + vaqt_qadami, aqi_i])
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


# ═══════════════════════════════════════════════════════════════
# O'RGATISH
# ═══════════════════════════════════════════════════════════════

def orgatish(
    model: nn.Module,
    X_train: np.ndarray, y_train: np.ndarray,
    X_val:   np.ndarray, y_val:   np.ndarray,
) -> dict:
    """
    PyTorch o'rgatish sikli.
    EarlyStopping va ReduceLROnPlateau o'rnatilgan.
    """
    criterion = nn.HuberLoss()    # Outlier larga chidamli
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, factor=0.5, patience=6, min_lr=1e-6
    )

    # Tensor ga aylantirish
    X_tr = torch.tensor(X_train)
    y_tr = torch.tensor(y_train).unsqueeze(1)
    X_vl = torch.tensor(X_val)
    y_vl = torch.tensor(y_val).unsqueeze(1)

    loader = DataLoader(TensorDataset(X_tr, y_tr), batch_size=BATCH_SIZE, shuffle=True)

    tarix = {"loss": [], "val_loss": [], "mae": [], "val_mae": []}

    eng_yaxshi_loss = float("inf")
    eng_yaxshi_holat = None
    sabr_hisobi = 0

    model.train()
    for epoch in range(1, EPOCHS + 1):
        # ── O'rgatish ──
        model.train()
        epoch_loss, epoch_mae = 0.0, 0.0
        for xb, yb in loader:
            optimizer.zero_grad()
            pred = model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            epoch_loss += loss.item() * len(xb)
            epoch_mae  += (pred - yb).abs().sum().item()

        epoch_loss /= len(X_train)
        epoch_mae  /= len(X_train)

        # ── Validatsiya ──
        model.eval()
        with torch.no_grad():
            val_pred = model(X_vl)
            val_loss = criterion(val_pred, y_vl).item()
            val_mae  = (val_pred - y_vl).abs().mean().item()

        tarix["loss"].append(epoch_loss)
        tarix["val_loss"].append(val_loss)
        tarix["mae"].append(epoch_mae)
        tarix["val_mae"].append(val_mae)

        scheduler.step(val_loss)

        # ── EarlyStopping ──
        if val_loss < eng_yaxshi_loss - 1e-5:
            eng_yaxshi_loss  = val_loss
            eng_yaxshi_holat = {k: v.clone() for k, v in model.state_dict().items()}
            sabr_hisobi = 0
        else:
            sabr_hisobi += 1

        if epoch % 10 == 0:
            lr = optimizer.param_groups[0]["lr"]
            print(f"  Epoch {epoch:3d}/{EPOCHS} | loss={epoch_loss:.5f} "
                  f"val_loss={val_loss:.5f} | mae={epoch_mae:.3f} "
                  f"val_mae={val_mae:.3f} | lr={lr:.6f}")

        if sabr_hisobi >= PATIENCE:
            print(f"  EarlyStopping: {epoch} epochda to'xtatildi (patience={PATIENCE})")
            break

    # Eng yaxshi holat ni tiklash
    if eng_yaxshi_holat:
        model.load_state_dict(eng_yaxshi_holat)

    return tarix


# ═══════════════════════════════════════════════════════════════
# BAHOLASH
# ═══════════════════════════════════════════════════════════════

def metrikalar_hisoblash(y_haq: np.ndarray, y_bas: np.ndarray) -> dict:
    return {
        "MAE":  float(mean_absolute_error(y_haq, y_bas)),
        "RMSE": float(np.sqrt(mean_squared_error(y_haq, y_bas))),
        "R2":   float(r2_score(y_haq, y_bas)),
    }


def teskari_masshtablash(y_sk: np.ndarray, scaler: MinMaxScaler) -> np.ndarray:
    """Faqat AQI ustunini original o'lchamga qaytarish."""
    aqi_i        = FEATURES.index(TARGET)
    temp         = np.zeros((len(y_sk), len(FEATURES)), dtype=np.float32)
    temp[:, aqi_i] = y_sk
    return scaler.inverse_transform(temp)[:, aqi_i]


# ═══════════════════════════════════════════════════════════════
# GRAFIKLAR
# ═══════════════════════════════════════════════════════════════

def grafiklar_saqlash(tarix: dict, y_test: np.ndarray,
                      y_pred: np.ndarray, metrikalar: dict) -> None:
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        "LSTM Model — Havo Sifati AQI Bashorati\nDiplom ishi, 2025-2026",
        fontsize=14, fontweight="bold", y=0.98,
    )

    # 1. Loss grafigi
    ax = axs[0, 0]
    ax.plot(tarix["loss"],     label="O'rgatish",   color="#3b82f6", linewidth=2)
    ax.plot(tarix["val_loss"], label="Validatsiya", color="#ef4444", linewidth=2)
    ax.set_title("O'rgatish jarayoni (Huber Loss)")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss")
    ax.legend(); ax.grid(True, alpha=0.3)

    # 2. MAE grafigi
    ax = axs[0, 1]
    ax.plot(tarix["mae"],     label="O'rgatish MAE",   color="#10b981", linewidth=2)
    ax.plot(tarix["val_mae"], label="Validatsiya MAE", color="#f59e0b", linewidth=2)
    ax.set_title("O'rtacha Absolut Xato (MAE)")
    ax.set_xlabel("Epoch"); ax.set_ylabel("MAE (AQI)")
    ax.legend(); ax.grid(True, alpha=0.3)

    # 3. Bashorat vs Haqiqiy
    ax = axs[1, 0]
    n = min(168, len(y_test))
    ax.plot(y_test[-n:], label="Haqiqiy AQI",  color="#3b82f6", alpha=0.85, linewidth=1.5)
    ax.plot(y_pred[-n:], label="Bashorat AQI", color="#ef4444",
            linestyle="--", alpha=0.85, linewidth=1.5)
    ax.set_title(f"Bashorat vs Haqiqiy (oxirgi {n} soat)")
    ax.set_xlabel("Vaqt (soat)"); ax.set_ylabel("AQI")
    ax.legend(); ax.grid(True, alpha=0.3)

    # 4. Korrelyatsiya scatter
    ax = axs[1, 1]
    ax.scatter(y_test, y_pred, alpha=0.35, s=8, color="#8b5cf6")
    mn = min(y_test.min(), y_pred.min())
    mx = max(y_test.max(), y_pred.max())
    ax.plot([mn, mx], [mn, mx], "r--", linewidth=2, label="Ideal (y=x)")
    ax.set_title("Korrelyatsiya: Bashorat vs Haqiqiy")
    ax.set_xlabel("Haqiqiy AQI"); ax.set_ylabel("Bashorat AQI")
    matn = (f"MAE  = {metrikalar['MAE']:.2f} AQI\n"
            f"RMSE = {metrikalar['RMSE']:.2f} AQI\n"
            f"R²   = {metrikalar['R2']:.4f}")
    ax.text(0.05, 0.95, matn, transform=ax.transAxes, verticalalignment="top",
            fontfamily="monospace", fontsize=10,
            bbox={"boxstyle": "round,pad=0.4", "facecolor": "#fef3c7", "alpha": 0.9})
    ax.legend(); ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(GRAFIK_YOLI, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"✅ Grafik saqlandi: {GRAFIK_YOLI}")


# ═══════════════════════════════════════════════════════════════
# ASOSIY
# ═══════════════════════════════════════════════════════════════

def main() -> dict:
    print("=" * 58)
    print("  LSTM Model O'rgatish — Havo Sifati AQI Bashorati")
    print("=" * 58)

    # 1. Ma'lumot yuklash
    df = csv_yuklash()
    print(f"   AQI: min={df['aqi'].min():.0f}, max={df['aqi'].max():.0f}, "
          f"o'rta={df['aqi'].mean():.1f}")

    # 2. Masshtablash (faqat train qismiga fit!)
    chegara = int(len(df) * TRAIN_NISBATI)
    scaler  = MinMaxScaler(feature_range=(0, 1))
    scaler.fit(df.iloc[:chegara][FEATURES].values)
    skalyangan = scaler.transform(df[FEATURES].values).astype(np.float32)

    # 3. Ketma-ketliklar
    X, y = ketma_ketlik_yaratish(skalyangan, VAQT_QADAMI)
    print(f"\n📐 Dataset shakli:")
    print(f"   X: {X.shape}  (namunalar × vaqt_qadami × xususiyatlar)")
    print(f"   y: {y.shape}")

    # 4. Train/Val/Test bo'lish
    n       = len(X)
    tr_end  = int(n * TRAIN_NISBATI)
    val_end = tr_end + int(n * 0.10)

    X_train, y_train = X[:tr_end],        y[:tr_end]
    X_val,   y_val   = X[tr_end:val_end], y[tr_end:val_end]
    X_test,  y_test  = X[val_end:],       y[val_end:]

    print(f"\n📊 Train/Val/Test:")
    print(f"   Train: {len(X_train):,} | Val: {len(X_val):,} | Test: {len(X_test):,}")

    # 5. Model
    model = LSTMModel(input_size=len(FEATURES)).to(DEVICE)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"\n🧠 Model parametrlari: {total_params:,}")

    # 6. O'rgatish
    print(f"\n🚀 O'rgatish boshlandi (max {EPOCHS} epoch, batch={BATCH_SIZE})...")
    tarix = orgatish(model, X_train, y_train, X_val, y_val)

    # 7. Test baholash
    model.eval()
    with torch.no_grad():
        y_pred_sc = model(torch.tensor(X_test)).squeeze().numpy()

    y_test_orig = teskari_masshtablash(y_test,    scaler)
    y_pred_orig = teskari_masshtablash(y_pred_sc, scaler)

    metrikalar = metrikalar_hisoblash(y_test_orig, y_pred_orig)

    print("\n" + "=" * 50)
    print("  📊 O'RGATISH NATIJALARI")
    print("=" * 50)
    print(f"  MAE  (O'rtacha absolut xato) : {metrikalar['MAE']:8.3f} AQI birligi")
    print(f"  RMSE (Kvadrat xato ildizi)   : {metrikalar['RMSE']:8.3f} AQI birligi")
    print(f"  R²   (Determinatsiya koeff.) : {metrikalar['R2']:8.4f}")
    print("=" * 50)

    # 8. Saqlash
    torch.save({
        "model_state_dict": model.state_dict(),
        "input_size":  len(FEATURES),
        "hidden1":     64,
        "hidden2":     32,
        "dropout":     0.2,
        "vaqt_qadami": VAQT_QADAMI,
        "features":    FEATURES,
        "metrikalar":  metrikalar,
    }, MODEL_YOLI)
    print(f"\n✅ Model saqlandi    : {MODEL_YOLI}")

    joblib.dump(scaler, SCALER_YOLI)
    print(f"✅ Scaler saqlandi   : {SCALER_YOLI}")

    # 9. Grafiklar
    grafiklar_saqlash(tarix, y_test_orig, y_pred_orig, metrikalar)

    print(f"\n✨ Barcha natijalar tayyor!")
    print(f"   Grafik: {GRAFIK_YOLI}")
    print(f"\n   Keyingi qadam: python server.py  (LSTM avtomatik yuklanadi)")
    return metrikalar


if __name__ == "__main__":
    main()
