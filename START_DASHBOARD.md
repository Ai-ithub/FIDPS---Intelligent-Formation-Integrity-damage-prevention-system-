# 🚀 راهنمای اجرای Dashboard

برای اجرای Dashboard React.js، باید یکی از این روش‌ها را انتخاب کنید:

---

## روش 1: نصب Node.js و اجرای Development Mode (پیشنهادی)

### مرحله 1: نصب Node.js

اگر Node.js نصب نیست:

1. به سایت https://nodejs.org بروید
2. نسخه LTS (مثلاً 18.x یا 20.x) را دانلود کنید
3. فایل installer را اجرا کنید
4. پس از نصب، PowerShell را restart کنید

### مرحله 2: بررسی نصب

PowerShell جدید باز کنید و این دستورات را اجرا کنید:

```powershell
node --version
npm --version
```

باید نسخه Node.js و npm نمایش داده شود.

### مرحله 3: نصب Dependencies و اجرای Dashboard

```powershell
# رفتن به دایرکتوری frontend-react
cd frontend-react

# نصب dependencies
npm install --legacy-peer-deps

# اجرای dev server
npm run dev
```

Dashboard در `http://localhost:5173` باز می‌شود.

---

## روش 2: استفاده از Docker (اگر Docker نصب دارید)

اگر Docker Desktop روی سیستم شما نصب است:

```powershell
# از root directory پروژه
docker-compose up frontend-react

# یا برای همه سرویس‌ها
docker-compose up
```

Dashboard در `http://localhost` باز می‌شود.

---

## روش 3: نصب Docker Desktop (اگر ندارید)

### Windows:

1. دانلود Docker Desktop: https://www.docker.com/products/docker-desktop
2. نصب و راه‌اندازی
3. پس از نصب، Docker Desktop را باز کنید
4. سپس از روش 2 استفاده کنید

---

## 🔍 بررسی مشکلات

### مشکل: npm پیدا نمی‌شود

**راه حل:**
1. Node.js را دوباره نصب کنید
2. PowerShell را restart کنید
3. PATH را بررسی کنید:
   ```powershell
   $env:PATH -split ';' | Select-String node
   ```

### مشکل: Port در حال استفاده است

**راه حل:**
```powershell
# Port را در vite.config.ts تغییر دهید:
# server: { port: 5174 }
```

### مشکل: Backend متصل نمی‌شود

**راه حل:**
1. مطمئن شوید Backend API در حال اجرا است
2. بررسی کنید: `http://localhost:8000/health`
3. اگر اجرا نیست، backend را راه‌اندازی کنید

---

## ✅ بعد از اجرا

پس از اجرای موفق، باید:

1. ✅ صفحه Dashboard در مرورگر باز شود
2. ✅ Connection status "Connected" نشان دهد
3. ✅ Metrics نمایش داده شوند
4. ✅ Navigation کار کند

---

## 🎯 Quick Start (اگر Node.js نصب دارید)

```powershell
# از root directory
cd frontend-react
npm install --legacy-peer-deps
npm run dev
```

سپس مرورگر را باز کنید: **http://localhost:5173**

---

## 📞 اگر هنوز مشکل دارید

1. مطمئن شوید Node.js 18+ نصب است
2. PowerShell را با Administrator rights اجرا کنید
3. Firewall را بررسی کنید
4. Antivirus را موقتاً disable کنید (برای تست)

---

**نکته:** اگر نمی‌خواهید Node.js نصب کنید، می‌توانید از Docker استفاده کنید یا از یک سیستم دیگر که Node.js دارد استفاده کنید.

