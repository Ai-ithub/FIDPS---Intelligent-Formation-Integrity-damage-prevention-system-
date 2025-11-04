# راهنمای اجرای Dashboard بدون اینترنت (Offline Mode)

## روش 1: اجرای مستقیم (نیاز به دانلود Chart.js)

### مرحله 1: دانلود Chart.js

1. فایل Chart.js را از یکی از آدرس‌های زیر دانلود کنید:
   - **CDN Link**: https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js
   - **یا از سایت رسمی**: https://www.chartjs.org/docs/latest/getting-started/installation.html

2. فایل دانلود شده را در همان پوشه‌ای که `dashboard-html-demo.html` قرار دارد، ذخیره کنید و نام آن را `chart.umd.min.js` بگذارید.

### مرحله 2: تغییر فایل HTML

فایل `dashboard-html-demo.html` را باز کنید و خط زیر را پیدا کنید:

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
```

آن را به این تغییر دهید:

```html
<script src="./chart.umd.min.js"></script>
```

### مرحله 3: اجرا

1. اتصال اینترنت خود را قطع کنید
2. روی فایل `dashboard-html-demo.html` دبل کلیک کنید
3. Dashboard در مرورگر باز می‌شود و بدون نیاز به اینترنت کار می‌کند

---

## روش 2: اجرا با Fallback (اگر Chart.js دانلود نشده)

فایل `dashboard-html-demo.html` قبلاً یک fallback mechanism دارد که در صورت عدم دسترسی به CDN، از یک نسخه ساده استفاده می‌کند.

**توجه**: این روش عملکرد محدودی دارد و نمودارها ممکن است به درستی نمایش داده نشوند.

---

## روش 3: اجرا با استفاده از Local Server (پیشنهادی)

### استفاده از Python (اگر نصب است):

1. در Command Prompt یا PowerShell به پوشه فایل بروید:
```bash
cd "C:\Users\asus\Documents\companies\ithub\AI\products\clones\fidps\FIDPS---Intelligent-Formation-Integrity-damage-prevention-system-"
```

2. یک سرور محلی راه‌اندازی کنید:

**Python 3:**
```bash
python -m http.server 8000
```

**Python 2:**
```bash
python -m SimpleHTTPServer 8000
```

3. مرورگر را باز کنید و به آدرس زیر بروید:
```
http://localhost:8000/dashboard-html-demo.html
```

### استفاده از Node.js (اگر نصب است):

1. نصب http-server:
```bash
npm install -g http-server
```

2. اجرا در پوشه فایل:
```bash
http-server -p 8000
```

3. باز کردن در مرورگر:
```
http://localhost:8000/dashboard-html-demo.html
```

---

## روش 4: ایجاد نسخه کاملاً Standalone

برای ایجاد یک نسخه کاملاً standalone که هیچ وابستگی خارجی ندارد:

### مرحله 1: دانلود Chart.js

از این لینک دانلود کنید:
```
https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js
```

### مرحله 2: Embed مستقیم در HTML

می‌توانید محتوای فایل `chart.umd.min.js` را مستقیماً در فایل HTML قرار دهید (این کار فایل را بزرگ می‌کند اما کاملاً standalone می‌شود).

---

## نکات مهم:

1. **بهترین روش**: روش 1 (دانلود Chart.js و استفاده محلی) است
2. **راه سریع**: استفاده از local server (روش 3) - حتی بدون اینترنت کار می‌کند اگر Chart.js را قبلاً دانلود کرده باشید
3. **Save Dashboard**: دکمه "Save Dashboard" در بالای صفحه داده‌ها را در فایل JSON ذخیره می‌کند و همچنین در localStorage مرورگر ذخیره می‌شود
4. **Data Persistence**: داده‌های ذخیره شده در localStorage حتی بعد از بستن مرورگر باقی می‌مانند

---

## ساختار فایل‌های مورد نیاز:

```
FIDPS---Intelligent-Formation-Integrity-damage-prevention-system-/
├── dashboard-html-demo.html    (فایل اصلی Dashboard)
├── chart.umd.min.js            (فایل Chart.js - باید دانلود شود)
└── OFFLINE-DASHBOARD-GUIDE.md  (این راهنما)
```

---

## راهنمای سریع (Quick Start):

1. **دانلود Chart.js:**
   - مرورگر را باز کنید و به این آدرس بروید: `https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js`
   - با راست کلیک → Save As → فایل را در همان پوشه `dashboard-html-demo.html` ذخیره کنید

2. **تغییر فایل HTML:**
   - `dashboard-html-demo.html` را با Notepad یا VS Code باز کنید
   - خط 8-20 را پیدا کنید که مربوط به script Chart.js است
   - به جای CDN link، از `./chart.umd.min.js` استفاده کنید

3. **اجرا:**
   - روی فایل `dashboard-html-demo.html` دبل کلیک کنید
   - Dashboard بدون نیاز به اینترنت اجرا می‌شود!

---

## پشتیبانی:

اگر مشکلی پیش آمد، بررسی کنید:
- ✅ آیا فایل `chart.umd.min.js` در همان پوشه HTML قرار دارد؟
- ✅ آیا مسیر فایل در تگ `<script>` درست است؟
- ✅ آیا Console مرورگر (F12) خطایی نشان می‌دهد؟
