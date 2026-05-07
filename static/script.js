/* ═══════════════════════════════════════════════════
   Havo Sifati Monitoringi — Umumiy JavaScript utilitalar
   ═══════════════════════════════════════════════════ */

/**
 * ISO vaqt satrini to'liq ko'rinishda formatlash (Toshkent vaqti).
 * Masalan: "07.05.2025 14:30:25"
 */
function vaqtFormatla(isoStr) {
  if (!isoStr) return '—';
  try {
    return new Date(isoStr).toLocaleString('uz-UZ', {
      timeZone: 'Asia/Tashkent',
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
  } catch { return isoStr; }
}

/**
 * ISO vaqt satridan faqat soat:daqiqa olish.
 * Masalan: "14:30"
 */
function faqatVaqt(isoStr) {
  if (!isoStr) return '—';
  try {
    return new Date(isoStr).toLocaleTimeString('uz-UZ', {
      timeZone: 'Asia/Tashkent',
      hour: '2-digit', minute: '2-digit',
    });
  } catch { return isoStr.slice(11, 16); }
}

/**
 * AQI qiymatiga mos rang qaytarish.
 */
function aqiRangi(aqi) {
  if (aqi == null) return '#64748b';
  if (aqi <= 50)  return '#10b981';
  if (aqi <= 100) return '#f59e0b';
  if (aqi <= 150) return '#f97316';
  if (aqi <= 200) return '#ef4444';
  if (aqi <= 300) return '#8b5cf6';
  return '#78350f';
}

/**
 * Sensor chip HTML yaratish (binary sensor uchun).
 * qiymat: 1 = toza, 0 = gaz, null = ulanmagan
 */
function sensorChip(qiymat) {
  if (qiymat === null || qiymat === undefined)
    return '<span class="chip kulrang">━ Ulanmagan</span>';
  if (qiymat === 1)
    return '<span class="chip yashil">✔ Toza</span>';
  return '<span class="chip qizil puls">⚠ Gaz!</span>';
}

/**
 * Analog sensor qiymatini formatlash (harorat, pm va h.k.).
 */
function analogChip(qiymat, birlik) {
  if (qiymat === null || qiymat === undefined)
    return '<span class="chip kulrang">━ Ulanmagan</span>';
  return `<span class="chip yashil">${parseFloat(qiymat).toFixed(1)} ${birlik}</span>`;
}

/**
 * Aktiv navigatsiya havolasini belgilash (joriy URL asosida).
 */
function navHighlight() {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.toggle('active', link.getAttribute('href') === path);
  });
}

// Sahifa yuklanganda navni to'g'irlash
document.addEventListener('DOMContentLoaded', navHighlight);
