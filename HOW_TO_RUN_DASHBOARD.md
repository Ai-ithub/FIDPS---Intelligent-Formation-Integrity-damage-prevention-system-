# 🚀 چگونه Dashboard را اجرا کنیم؟

## ⚠️ وضعیت فعلی

برای اجرای Dashboard React.js، شما نیاز به **Node.js** دارید که فعلاً روی سیستم شما نصب نیست.

---

## ✅ راه حل‌های پیشنهادی

### روش 1: نصب Node.js (پیشنهادی - 5 دقیقه)

#### گام 1: دانلود Node.js
1. به آدرس زیر بروید: **https://nodejs.org**
2. روی دکمه **"Download Node.js (LTS)"** کلیک کنید
3. فایل installer را دانلود کنید (Windows Installer .msi)

#### گام 2: نصب
1. فایل دانلود شده را اجرا کنید
2. مراحل نصب را دنبال کنید (Next, Next, Install)
3. **⚠️ مهم:** پس از نصب، PowerShell یا Terminal را **بست** و دوباره **باز** کنید

#### گام 3: اجرای Dashboard
PowerShell جدید را باز کنید و این دستورات را اجرا کنید:

```powershell
# رفتن به دایرکتوری پروژه
cd "C:\Users\asus\Documents\companies\ithub\AI\products\clones\fidps\FIDPS---Intelligent-Formation-Integrity-damage-prevention-system-"

# اجرای اسکریپت خودکار
.\start-dashboard.ps1
```

یا دستی:

```powershell
cd frontend-react
npm install --legacy-peer-deps
npm run dev
```

Dashboard در `http://localhost:5173` باز می‌شود! 🎉

---

### روش 2: استفاده از اسکریپت خودکار

پس از نصب Node.js، اسکریپت `start-dashboard.ps1` را اجرا کنید:

```powershell
.\start-dashboard.ps1
```

این اسکریپت به صورت خودکار:
- ✅ Node.js را بررسی می‌کند
- ✅ Dependencies را نصب می‌کند (اگر لازم باشد)
- ✅ Backend را چک می‌کند
- ✅ Dashboard را اجرا می‌کند

---

### روش 3: استفاده از Docker (اگر Docker نصب دارید)

اگر Docker Desktop روی سیستم شماست:

```powershell
docker-compose up frontend-react
```

Dashboard در `http://localhost` باز می‌شود.

---

## 🔍 بررسی نصب Node.js

پس از نصب، این دستورات را در PowerShell جدید اجرا کنید:

```powershell
node --version
npm --version
```

باید چیزی شبیه این نمایش داده شود:
```
v20.10.0
10.2.3
```

---

## 📋 چک‌لیست

قبل از اجرا، مطمئن شوید:

- [ ] Node.js 18+ نصب شده
- [ ] PowerShell را restart کرده‌اید (پس از نصب Node.js)
- [ ] در دایرکتوری root پروژه هستید
- [ ] Internet connection دارید (برای npm install)

---

## 🎯 پس از اجرا

پس از اجرای موفق `npm run dev`:

1. ✅ یک پیغام مشابه این می‌بینید:
   ```
   VITE v5.0.8  ready in 500 ms

   ➜  Local:   http://localhost:5173/
   ➜  Network: use --host to expose
   ```

2. ✅ مرورگر را باز کنید: **http://localhost:5173**

3. ✅ Dashboard باید نمایش داده شود!

---

## 🆘 اگر مشکل داشتید

### مشکل: "npm is not recognized"
**راه حل:** PowerShell را restart کنید

### مشکل: Port 5173 in use
**راه حل:** در `frontend-react/vite.config.ts` port را تغییر دهید

### مشکل: Cannot install dependencies
**راه حل:** 
```powershell
npm install --legacy-peer-deps --force
```

### مشکل: Backend connection failed
**راه حل:** Backend را اجرا کنید:
```powershell
# از root directory
docker-compose up api-dashboard
```

---

## 📞 نیاز به کمک بیشتر؟

1. فایل `START_DASHBOARD.md` را مطالعه کنید
2. فایل `FRONTEND_QUICKSTART.md` را ببینید
3. Console browser را برای خطاها چک کنید

---

**خلاصه:**
1. Node.js را از nodejs.org نصب کنید
2. PowerShell را restart کنید  
3. `.\start-dashboard.ps1` را اجرا کنید
4. Dashboard در مرورگر باز می‌شود! 🎉

