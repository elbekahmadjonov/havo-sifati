@echo off
chcp 65001 > nul
title Havo Sifati Monitoringi v2.0

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   Havo Sifati Monitoringi — v2.0            ║
echo  ║   Diplom loyihasi, 2025                     ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: Python tekshirish
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo  [XATO] Python topilmadi!
    echo  https://python.org dan yuklab o'rnating.
    pause & exit /b 1
)
echo  [OK] Python topildi

:: Paketlarni o'rnatish
echo  [->] Paketlar tekshirilmoqda...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo  [XATO] Paketlar o'rnatilmadi!
    pause & exit /b 1
)
echo  [OK] Barcha paketlar tayyor

:: .env fayli mavjudligini tekshirish
if not exist ".env" (
    if exist ".env.example" (
        echo  [!] .env fayli yo'q. .env.example dan nusxa olindi.
        copy .env.example .env > nul
    )
)

:: IP manzilni ko'rsatish
echo.
echo  ─────────────────────────────────────────────────
echo  [!] Kompyuteringizning Wi-Fi IP manzili:
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /i "IPv4"') do (
    echo      %%i
)
echo.
echo  [!] ESP32 da SERVER_URL ni shu IP ga o'zgartiring:
echo      http://[IP_MANZIL]:8000/api/sensor
echo  [!] Dashboard: http://localhost:8000
echo  ─────────────────────────────────────────────────
echo.

:: Brauzerda ochish
echo  [->] Brauzer 4 sekunddan keyin ochiladi...
timeout /t 4 /nobreak > nul
start http://localhost:8000

:: Serverni ishga tushirish
echo  [->] Server ishga tushirilmoqda...
echo.
python server.py

echo.
echo  [!] Server to'xtatildi.
pause
